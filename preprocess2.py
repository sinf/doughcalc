#!/usr/bin/python3
# A preprocessing script for generating a xhtml web page with python code
# (c) 2020 Arho Mahlamäki
# This code is licensed under GPL v3.

import re
import sys
import os
from traceback import format_exception
from io import StringIO
from mimetypes import guess_type as guess_mime
from base64 import b64encode
from glob import glob
from hashlib import sha256
from css_html_js_minify import html_minify, js_minify, css_minify
import urllib.parse
import xml.etree.ElementTree as ET
#from lxml import etree as ET

LANG='fi'
DEPS=[]
def newdep(x):
    DEPS.add(x)

class Fob:
    def __init__(self,path):
        self.path = path
        newdep(path)
        with open(path,'r') as f:
            self.data = f.read()
    def __str__(self):
        return self.data

class XHTML_Header:
    def __init__(self,meta,title,xtags):
        self.meta = meta
        self.title = title
        self.xtags = xtags
    def __str__(self):
        m='<?xml version="1.0" encoding="UTF-8"?>\n' +
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n' +
            '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="%s" lang="%s">' % (LANG, LANG) +
        '<head>' +
        '<meta charset="UTF-8"/>' +
        '<meta http-equiv="Content-Type" content="application/xhtml+xml; charset=UTF-8"/>' +
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, shrink-to-fit=no"/>' +
        '<meta http-equiv="X-UA-Compatible" content="IE=edge"/>'
        for x in self.meta.items():
            m += '<meta name="%s" content="%s"/>' % x
        m += '<link rel="icon" href=%s/>' % datauri('favicon.gif')
        m += '<title>' + self.title + '</title>'
        m += ''.join(self.xtags)
        m += '</head>'

class Xstr:
    def __init__(self, s):
        self.s = s
    def __str__(self):
        s='<span>'
        for i in self.s.items():
            s += '<span class="%s">%s</span>' % i
        s += '</span>'

def urlenc(url):
    return urllib.parse.quote_plus(url)

from preprocess_util import *

INCDIRS=('inc','inc/svg-inline','inc/auto-out','www','src','src/svg-sass','.')
LANG_CC='fi'
deps=set()
strings_a={}
strings_b={}
macros={}

"""
all txt files in strings/ directory contain strings and macros

--- recursive things, evaluated first, iteratively ---

@@stringId$
    recursively substitute with a localized string
    string definition (may include newlines):
        stringId[:langCC]=translatedString<<

=INCL:filepath$
    substitute with contents of a text file

$macroName(value1,value2,...)
    evaluate macro recursively
    macro definition (may include newlines):
        macroName(param1 param2 ...)=.....<<

--- non-recursive functions, evaluated last ---

@LOCL:filepath$
    transform path to localized variant if that file exist

@DATA:filepath$
    load (possibly localized) file and convert to base64 data uri

@JSINCL:filepath$
    substitute with contents of javascript file
    wrap in CDATA

@FVER:filepath$
    reference to some local file with checksum as version number
    "filepath?v=xxxxxxx"


;py\\  code  \\py;

"""

def load_strings(filepath):
    with open(filepath,'r') as fil:
        text=fil.read()
        for obj in re.finditer(r'^(\w+)(:[a-z]+)?=(.*?)<<\n', text, re.M|re.S):
            k=obj.group(1)
            v=(obj.group(3),filepath)
            lc=obj.group(2)
            lc=lc[1:] if lc else ''
            if lc not in strings_b:
                strings_b[lc] = {k:v}
            else:
                strings_b[lc][k] = v
        for obj in re.finditer(r'^(\w+)\(([^)]*)\)=(.*?)<<\n', text, re.M|re.S):
            k=obj.group(1)
            a=obj.group(2)
            a=a.split(',') if a else []
            a=[x.strip() for x in a]
            v=obj.group(3)
            macros[k] = (a,v)

def newdep(x):
    global deps
    deps.add(x)

def getstr(str_id,lang0=None):
    global LANG_CC, strings_a, strings_b, missing
    la=LANG_CC if lang0 is None else lang0
    for cc in (la,''):
        if cc in strings_b:
            xx=strings_b[cc]
            if str_id in xx:
                yy=xx[str_id]
                newdep(yy[1])
                return yy[0]
    if str_id in strings_a:
        return strings_a[str_id]
    print(str_id, ':', la, '=xxxxx<<<',sep='',file=missing)
    return 'UNTRANSLATED[%s]' % str_id

def get_translation(obj):
    return getstr(obj.group(1))

def warn(*msg):
    print("\033[1;31mWarning:",*msg,"\033[0m",file=sys.stderr)

def fail(*msg, sep=' '):
    print("\033[1;31mError:",*msg,"\033[0m",file=sys.stderr,sep=sep)
    sys.exit(1)

def datauri_nq(path):
    for d in INCDIRS:
        p2=os.path.join(d,path)
        if os.path.isfile(p2):
            with open(p2,'rb') as f:
                data=b64encode(f.read()).decode('ASCII')
                return 'data:'+guess_mime(path)[0]+ \
                    ';base64,'+data+'';
    fail("DATAURI include file not found: " + path)

def datauri(path):
    return '"' + datauri_nq(path) + '"'

def inline_url(filename):
    return 'url(' + datauri(filename) + ')'

def datauri_nq_obj(obj):
    return datauri_nq(obj.group(1))

def datauri_obj(obj):
    return datauri(obj.group(1))

def HintaSa(i,f):
    return '<span class="HintaSa">%d<span>,</span><sup>%02d</sup></span>' % (int(i),int(f))

def HintaSa2(xx,i,f):
    return '<li><span>'+xx+'</span>'+HintaSa(i,f)+'</li>'

def Hinnat(xyz):
    append_page('<ul class="dotleaders">')
    for x,y,z in xyz:
        append_page(HintaSa2(getstr(x),y,z))
    append_page('</ul>')

def file_to_include(basename):
    base=basename
    if base.startswith('/'):
        base=base[1:]
    elif base.startswith('../'):
        base=base[3:]
    for d in INCDIRS:
        r=os.path.join(d,base)
        if os.path.isfile(r):
            newdep(r)
            return r
    fail('file to include was not found:',basename)

def read_file(basename):
    with open(file_to_include(basename),'r') as f:
        return f.read().strip()

def minihash(text):
    """ get some hashcode of a string """
    x=sha256();
    x.update(text.strip().encode())
    return x.hexdigest()[:8]

def fminihash(filepath):
    """ used for versioning hrefs """
    return minihash(read_file(filepath))

def FVER(path):
    return '"%s?v=%s"' % (path, fminihash(path))

def CSSIMGHASH(path):
    print("url(%s?v=%s)" % (path, fminihash(path)))

def fver_obj(obj):
    return FVER(obj.group(1))

def INCL(basename):
    """ insert contents of a file, but process it recursively """
    print(process_text(read_file(basename)),end='')

def LINK_CSS(basename,v=True):
    """ reference a stylesheet (in <head>) """
    ver='' if not v else '?v='+fminihash(basename)
    print(
    '<link rel="stylesheet" type="text/css" href="/%s%s"/>'
    % (basename, ver))

def SCRIPT(basename, async=False):
    """ reference an external script """
    a=('',' async="async"')[async]
    print('<script type="text/javascript" src="/%s?v=%s"%s></script>'
    % (basename,fminihash(basename),a))

def htmlspecialchars(s):
    for a,b in (
        ("&","&amp;"),('"',"&quot;"),("<","&lt;"),(">","&gt;")
        ): s=s.replace(a,b);
    return s

def incl_f(path):
    return process_text(read_file(path))

def incl_f_obj(obj):
    return incl_f(obj.group(1))

def wrap_chars(string,tag,attrib={}):
    """ Wrap each character in string inside XML tag """
    s=''
    for c in string:
        s+=c if c.isspace() else mkTag(tag,attrib,c)
    return s

append_indent_val = 0;
def append_indent(n):
    global append_indent_val
    append_indent_val = n;

def append_page(*x, sep='', end=''):
    """ used from within inline python in source xhtml """
    print('\t'*append_indent_val, *x,sep=sep,end=end)

def wrap_cdata(x):
    return '<![CDATA[' + x + ']]>'

def inline_js(x):
    append_page('//<![CDATA[\n'+js_minify(read_file(x))+'//]]>')

def inline_css(x):
    append_page('<style type="text/css">/*<![CDATA[*/',
            read_file(x),
            '/*]]>*/</style>')

def inline_svg(x):
    # should also minify
    append_page(wrap_cdata(read_file(x)))

def mkTag(tag,attr={},inner=None):
    s='<' + tag
    for k,v in attr.items():
        if len(v) > 0:
            s += ' %s="%s"' % (k,v)
    if inner is not None:
        s = s + ">" + inner + "</" + tag + ">"
    else:
        s = s + '/>'
    return s

def Morgon(a,b=''):
    append_page( \
        wrap_chars(a,'span',{'class':'P'}), ' ', \
        wrap_chars(b,'span',{'class':'P o'}), '\n')

def setup(lc):
    global strings_a, deps, LANG_CC
    LANG_CC = lc
    strings_a = {'LANG':lc}
    deps = set()

def eval_stuff(match):
    codes=match.group(1)
    out0 = sys.stdout
    try:
        sys.stdout = StringIO()
        exec(codes, globals(), {})
        output=sys.stdout.getvalue()
    except:
        sys.stdout=out0
        ex=sys.exc_info()
        cdl=codes.split('\n')
        if len(cdl) > 10:
            cdl = cdl[:10] + ['...(continues)...']
        fail(*format_exception(*ex),
            '--- Relevant code: ---', *cdl,
            '----------------------',
            'file:'+getstr('FILE'), sep='\n');
    sys.stdout=out0
    return output

def reg_svg():
    for prefix,ns in [ \
('',"http://www.w3.org/2000/svg"), \
("svg","http://www.w3.org/2000/svg"), \
("xlink","http://www.w3.org/1999/xlink"), \
("rdf","http://www.w3.org/1999/02/22-rdf-syntax-ns#"), \
("dc","http://purl.org/dc/elements/1.1/"), \
("cc","http://creativecommons.org/ns#"), \
("sodipodi","http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"), \
("inkscape","http://www.inkscape.org/namespaces/inkscape")]:
        ET.register_namespace(prefix, ns)

def incl_svg(obj):
    """ inline svg according to HTML5 spec """
    fn=file_to_include(obj.group(1))
    try:
        reg_svg()
        x=ET.parse(fn)
    except ET.ParseError as ex:
        fail("xml parse error,", ex, sep='\n')
    for e in x.iter():
        to_del=[]
        for k in e.attrib.keys():
            if k.find('inkscape') >= 0:
                to_del += [k]
        for k in to_del:
            del e.attrib[k]
    #return ET.tostring(e, encoding="unicode", xml_declaration=False, pretty_print=True, method="xml")
    # python etree
    i=StringIO()
    x.write(i,encoding="unicode",xml_declaration=False,method='xml')
    return i.getvalue() \
        .replace('xmlns:svg="http://www.w3.org/2000/svg"', \
        'xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg"') \
        .replace('svg:','').strip();

def process_text(text):
    x=1
    while x:
        text,x=re.subn(r'@@(\w+)\$', get_translation, text)
    text=re.sub(r'=INCL:([^\$]*)\$', incl_f_obj, text)
    text=re.sub(r'@SVG:([^\$]*)\$', incl_svg, text)
    text=re.sub(r'@FVER:([^\$]*)\$', fver_obj, text)
    text=re.sub(r'@DATANQ:([^\$]*)\$', datauri_nq_obj, text)
    text=re.sub(r'@DATA:([^\$]*)\$', datauri_obj, text)
    text=re.sub(r';py\\\\\s*(.*?)\s*\\\\py;', eval_stuff, text, flags=re.MULTILINE | re.DOTALL);
    text=re.sub(r'/\*;py\\\\\s*(.*?)\s*\\\\py;\*/', eval_stuff, text, flags=re.MULTILINE | re.DOTALL);
    return text

def postprocess(text):
    # todo minify
    return text

def make_file(fn_unmin, fn_min, fn_dep, f_in, lc, basename):
    global strings_a
    setup(lc)
    strings_a['FILE'] = '/'+lc+'/'+basename
    with open(f_in,'r') as f:
        text = f.read()
    text=process_text(text)
    with open(fn_unmin,'w') as f:
        f.write(text)
    with open(fn_min,'w') as f:
        f.write(postprocess(text)) # todo minify
    with open(fn_dep,'w') as f:
        global deps
        print(fn_min+':',
            ' '.join('$(wildcard %s)' % x for x in deps),
            '\n',file=f)

def trydel(fn):
    try:
        os.path.remove(fn)
    except:
        pass

def main():
    """
    program args:
        basename languagecode
    reads
        src/basename
    writes
        www/languagecode/basename
        build_temp/basename.d
        build_temp/unmin/languagecode/basename
    """
    global strings_a, strings_b, LANG_CC, missing
    missing=open('log/missing_strings.txt','a')
    if sys.argv[1] == '--plain':
        f_in = sys.argv[2]
        f_out = sys.argv[min(3,len(sys.argv)-1)]
        with open(f_in,'r') as f:
            t=process_text(f.read())
        with open(f_out,'w') as f:
            f.write(t)
        return
    strings_b={}
    for f in glob("strings/*.txt"):
        load_strings(f)
    basen, cc = sys.argv[1], sys.argv[2]
    f_in = 'src/' + basen
    f_min = 'www/%s/%s' % (cc,basen)
    f_unmin = 'build_temp/%s/unmin/%s' % (cc,basen)
    f_dep = 'build_temp/%s/deps/%s.d' % (cc,basen)
    for f in (f_min, f_dep, f_unmin):
        trydel(f)
    make_file(f_unmin, f_min, f_dep, f_in, cc, basen)
    missing.close()
 
if __name__=="__main__":
    main()



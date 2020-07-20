
def FORM_IN_(name,max_char):
    return '<div class="lomake-input-inner"><input name="%s" size="%s" type="text"/></div>' % (name, max_char)

def FORM_IN(IIID,TITLE,AAA,S1):
    return '<tr id="%s">' % IIID +\
        '<td class="lomake-title">' + TITLE +\
        '</td><td colspan="2" class="lomake-input-ab">' +\
        FORM_IN_(AAA,S1) + '</td></tr>'

def FORM_IN2(IIID,TITLE,AAA,BBB,S1,S2):
    return '<tr id="%s">' % IIID +\
    '<td class="lomake-title">' + TITLE + '</td>' +\
    '<td class="lomake-input-a">' + FORM_IN_(AAA,S1) +'</td>' +\
    '<td class="lomake-input-b">' + FORM_IN_(BBB,S2) +'</td>' +\
    '</tr>'

def FORM_TEXTAREA(ROW_ID,TITLEMSG,INPUTNAME,NROWS,NCOLS):
    return '<tr id="%s" class="lomake-textarea-row">' % ROW_ID +\
    '<td class="lomake-title">'+TITLEMSG+'</td>' +\
    '<td colspan="2" class="lomake-input-ab">' +\
    '<textarea class="lomake-input-inner font2" name="%s" rows="%s" cols="%s">' % (INPUTNAME,NROWS,NCOLS) +\
    '</textarea></td></tr>'

def FORM_BOTTRAP(NNN):
    return '<tr style="opacity:0;font-size:0.0001em;height:0.0001em" class="dnone"><td colspan="3">I agree to terms and conditions<input class="nobotpls" name="%s" type="text" length="10"/></td></tr>' % NNN

def FORM_EHTO(AAA,BBB,XXX):
    return '<tr><td class="lomake-title">' +AAA +\
    '</td><td><input name="%s" type="checkbox"/>' %XXX +\
    '</td><td>'+BBB+'</td></tr>'


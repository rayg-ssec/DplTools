from sets import Set

setsfile='picnic/resources/portal_requestsets.json'

def formsetsForInstruments(instruments,subset):
    import json
    iset=Set(instruments)
    setlist=[]
    sets=json.load(file(setsfile))[subset]
    for aset in sets:
        if 'enabled' in aset and len(Set(aset['enabled']) & iset)==0:
            continue
        if 'required' in aset and len(Set(aset['required']) & iset)!=len(Set(aset['required'])):
            continue
        setlist.append(aset)

    return setlist

def makeUpdateFromData(asets):
    #print asets
    ret=''

    ret+="""
function updateFromData(availability){
    var itemlist = document.forms[0];
    fallbackTimeout=false;
    var av=new Array();
    var doall=false;
    if (availability && availability=='all')
      doall=true;
    if(availability && availability.length>0)
      av=availability.split(',');
      
"""
    for aset in asets:
        setid=0
        for setname in aset['order']:
            shoulden='true'
            if 'enabled' in aset['sets'][setname]:
                shoulden='||'.join(["hasString(av,'%s')"%s for s in aset['sets'][setname]['enabled']])
            if 'required' in aset['sets'][setname]:
                shoulden='&&'.join(["hasString(av,'%s')"%s for s in aset['sets'][setname]['required']])
            ret+="    doDisable(itemlist,'%s:%i',(!(%s))&&!doall);\n" % (aset['formname'],setid,shoulden)
            setid=setid+1
    ret+="""
    if(av.length>0)
      sanityCheckSubmit();
}
"""
    return ret





if __name__ == '__main__':
    print makeUpdateFromData(formsetsForInstruments(['lidar','radiosonde','baseline','merge','paeri0'],'images'))

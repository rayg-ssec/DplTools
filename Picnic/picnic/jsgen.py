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


def imagejavascriptgen(pathidx,instruments,dataAvailabilityPath):
 
    ret="""
var allDatasets='%s';
var datasetpath='%i';
var jspath='site';

var xmlhttp=false;

function getReq(){
//var xmlhttp=false;
if(xmlhttp){
  xmlhttp.abort();
  return xmlhttp;
}
/*@cc_on @*/
/*@if (@_jscript_version >= 5)
// JScript gives us Conditional compilation, we can cope with old IE versions.
// and security blocked creation of the objects.
 try {
  xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
 } catch (e) {
  try {
   xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
  } catch (E) {
   xmlhttp = false;
  }
 }
@end @*/
if (!xmlhttp && typeof XMLHttpRequest!='undefined') {
	try {
		xmlhttp = new XMLHttpRequest();
	} catch (e) {
		xmlhttp=false;
	}
}
if (!xmlhttp && window.createRequest) {
	try {
		xmlhttp = window.createRequest();
	} catch (e) {
		xmlhttp=false;
	}
}
return xmlhttp;
}

function hasString(arr,str){
  var i=0;
  for(i=0;i<arr.length;i++)
    if(arr[i]==str)
      return true;
  return false;
}

var enState=new Object();

function doDisable(objs,field,disable){
  if(field.length){//string
    fieldidx=field.split(':');
    if(fieldidx.length>1){
      field=fieldidx[0];
      idxes=fieldidx[1].split(',');
      f=objs[field];
      if(f==null)
        return;
      for(i=0;i<idxes.length;i++){
        idx=parseInt(idxes[i]);
        if(disable && !f[idx].disabled && f[idx].checked && (!enState.hasOwnProperty(field) || !f[enState[field]].disabled)){
          enState[field]=idx;
          //f[0].checked=true;
          setRadio(field,'none');
        }
        if(disable && idx==0)
          f.disabled=true;
        doDisable(f,idx,disable);
        if(!disable && idx==0)
          f.disabled=false;
        if(!disable && enState.hasOwnProperty(field) && enState[field]==idx)
          f[idx].checked=true;
      }
      return;
    }
  }

  var obj=objs[field];
  if(obj==null)
    return;
  var objt;
  if(obj.length)
    objt="array";
  else
    objt=obj.type.toLowerCase();
  wasDis=false;
  if(objt=="array")
    wasDis=obj[0].disabled;
  else
    wasDis=obj.disabled;
  if(disable==wasDis)
    return;
  if(disable){
    obj.disabled=true;
    if (objt == "array"){
      var vi=0;
      for(i=0;i<obj.length;i++){
        if(obj[i].checked)
          vi=i;
        doDisable(obj,i,true);
      }
      enState[field]=vi;
      obj[0].disabled=false;
      obj[0].checked=true;
    }else{
      obj.disabled=true;
    }
  }else{
    obj.disabled=false;
    if (objt == "array"){
      for(i=0;i<obj.length;i++)
        doDisable(obj,i,false);
      obj[enState[field]].checked=true;
    }else{
      obj.disabled=false;
    }
  }
}

function padString(str,filler,len){
 var ret="";
 while(ret.length+str.length<len)
   ret=ret+filler;
 ret=ret+str;
 return ret
}

function beginUpdating(){
  var itemlist = document.forms[0];
progressdisplay=document.getElementById('avail_progress');
progressdisplay.style.display="";
var sbmt=null;
for(i=0;i<itemlist.length;i++){
var tempobj = itemlist.elements[i];
if (tempobj.type.toLowerCase() == "submit")
sbmt=tempobj;
}
sbmt.disabled=true;
}

function finishUpdating(){
progressdisplay=document.getElementById('avail_progress');
progressdisplay.style.display="none";
}

var fallbackTimeout=false;
function sanityCheckSubmit() {
  itemlist=document.forms[0];
  var invcount=0;
  var sbmt=null;
  for(i=0;i<itemlist.length;i++){
     var tempobj = itemlist.elements[i];
     if (tempobj.type.toLowerCase() == "submit")
       sbmt=tempobj;
  }

  if(invcount>0){
    sbmt.disabled=true;
  }else{
    sbmt.disabled=false;
  }
}

%s

function clearFallback(){
    if(fallbackTimeout){
      clearTimeout(fallbackTimeout);
      fallbackTimeout=false;
    }
}
var countDownSeconds=0;
var countDownInterval=false;

function countDown(){
   if(!countDownInterval)
     countDownInterval=setInterval("countDown()",1000);
  document.getElementById("countdown").innerHTML = String(countDownSeconds);
  countDownSeconds=countDownSeconds-1;
  if(countDownSeconds<0){
    clearInterval(countDownInterval);
    countDownInterval=false;
  }
}

function checkDataAvailability() {
  var itemlist = document.forms[0];
  beginUpdating();
  //var dbg=itemlist['DEBUG'];
  var bstr=itemlist['byr'].value + padString(String(itemlist['bmo'].selectedIndex+1),'0',2) + padString(itemlist['bdy'].value,'0',2)  + 'T' + padString(itemlist['bhr'].value,'0',2) + padString(itemlist['bmn'].value,'0',2);
  var estr=itemlist['eyr'].value + padString(String(itemlist['emo'].selectedIndex+1),'0',2) + padString(itemlist['edy'].value,'0',2)  + 'T' + padString(itemlist['ehr'].value,'0',2) + padString(itemlist['emn'].value,'0',2);
  var availurl='%s?'+jspath+'='+datasetpath+'&time0='+bstr+'&time1='+estr;
  //dbg.value=availurl;
  r=getReq();
  r.open('GET',availurl,true);
  r.onreadystatechange=function(){
    if(r.readyState!=4)
      return;
    var availability = r.responseText;
    clearFallback();
    countDownSeconds=0;
    updateFromData(availability);
    finishUpdating();
   }
   clearFallback();
   countDownSeconds=15;
   countDown();
   fallbackTimeout=setTimeout("updateFromData('all')",countDownSeconds*1000);
   r.send(null);
}

function setRadio(name,value){
  var itemlist = document.forms[0];
  var cb=itemlist[name];
  for(i=0;i<cb.length;i++)
    if(cb[i].value==value){
      if(!cb[i].disabled)
        cb[i].checked=true;
      break;
    }
}


function showCustomEmail(){
  es=document.getElementById('emailset');
  es.style.display="none";
  ec=document.getElementById('emailcustom');
  ec.style.display="";
}
""" % (','.join(instruments),pathidx,makeUpdateFromData(formsetsForInstruments(instruments,'images')),dataAvailabilityPath)
    return ret


if __name__ == '__main__':
    print makeUpdateFromData(formsetsForInstruments(['lidar','radiosonde','baseline','merge','paeri0'],'images'))

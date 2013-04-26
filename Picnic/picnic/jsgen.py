from sets import Set

from HSRLImageArchiveLibrarian import HSRLImageArchiveLibrarian
lib=HSRLImageArchiveLibrarian(indexdefault='site')
from pyramid.view import view_config

@view_config(route_name='imagejavascript',renderer='string')
@view_config(route_name='netcdfjavascript',renderer='string')
def formjavascript(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    request.response.content_type='text/javascript'
    datasets=[]
    try:
        for inst in lib(**{methodtype:methodkey})['Instruments']:
            datasets.extend(lib.instrument(inst)['datasets'])
    except RuntimeError:
        return HTTPNotFound(methodtype + "-" + methodkey + " is invalid")
    if request.matched_route.name=='imagejavascript':
        return imagejavascriptgen(int(methodkey),datasets,request.route_path('dataAvailability'))
    return netcdfjavascriptgen(int(methodkey),datasets,request.route_path('dataAvailability'))

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
    var itemlist = document.forms['reqform'];
    fallbackTimeout=false;
    var av=new Array();
    var doall=false;
    var donone=false;
    var disabledSetting=false;
    if (itemlist['custom_display']!=null && itemlist['custom_display'].checked)
      donone=true;
    if (itemlist['allfields']!=null && itemlist['allfields'].checked){
      donone=true;
      disabledSetting=true;
    }
    if (availability && availability=='all')
      doall=true;
    if(availability && availability.length>0)
      av=availability.split(',');
      
"""
    for aset in asets:
        if 'order' in aset:
          setid=0
          for setname in aset['order']:
            shoulden='true'
            if 'enabled' in aset['sets'][setname]:
                shoulden='||'.join(["hasString(av,'%s')"%s for s in aset['sets'][setname]['enabled']])
            if 'required' in aset['sets'][setname]:
                shoulden='&&'.join(["hasString(av,'%s')"%s for s in aset['sets'][setname]['required']])
            ret+="    doDisable(itemlist,'%s:%i',((!(%s))&&!doall)||donone,disabledSetting);\n" % (aset['formname'],setid,shoulden)
            setid=setid+1
        else:
          for bset in aset['sets']:
            for cset in bset['options']:
              shoulden='true'
              if 'enabled' in cset:
                  shoulden='||'.join(["hasString(av,'%s')"%s for s in cset['enabled']])
              if 'required' in cset:
                  shoulden='&&'.join(["hasString(av,'%s')"%s for s in cset['required']])
              ret+="    doDisable(itemlist,'%s',((!(%s))&&!doall)||donone,disabledSetting);\n" % (cset['formname'],shoulden)
    ret+="""
    if(av.length>0)
      sanityCheckSubmit();
}
"""
    return ret

def netcdfjavascriptgen(pathidx,instruments,dataAvailabilityPath):
    psetKeys=['Dr','sigma_a','sigma_v','delta_a1','delta_v1','delta_a2','delta_v2','psettype']
    psets=[{'g_ice':'1','alpha_ice':'4','delta_v1':'3','psettype':'Solid Spheres','sigma_v':'1','alpha_water':'2','delta_a2':'2','delta_a1':'2','delta_v2':'3','g_water':'1','sigma_a':'1','Dr':'100'},
{'g_ice':'1','alpha_ice':'4','delta_v1':'3','psettype':'Fire II (Arnott 1994)','sigma_v':'0.266','alpha_water':'2','delta_a2':'1.27','delta_a1':'2','delta_v2':'2.26','g_water':'1','sigma_a':'0.76','Dr':'200'},
{'g_ice':'1','alpha_ice':'4','delta_v1':'2.91','psettype':'Hex Columns (Mitchell 1996)','sigma_v':'0.485','alpha_water':'2','delta_a2':'1.5','delta_a1':'2','delta_v2':'1.91','g_water':'1','sigma_a':'0.87','Dr':'100'},
{'g_ice':'1','alpha_ice':'4','delta_v1':'3','psettype':'Bullet Rosettes (Mitchell 1996)','sigma_v':'0.26','alpha_water':'2','g_water':'1','isdefault':'yes','delta_a1':'2','delta_v2':'2.26','delta_a2':'1.57','sigma_a':'1.0','Dr':'60'},
{'g_ice':'1','alpha_ice':'4','delta_v1':'2.42','psettype':'Stellar Crystal (Mitchell 1996)','sigma_v':'0.2','alpha_water':'2','delta_a2':'1.63','delta_a1':'1.85','delta_v2':'1.67','g_water':'1','sigma_a':'0.7','Dr':'90'},
{'g_ice':'1','alpha_ice':'4','delta_v1':'3','psettype':'Aggregates of Thin Plates (Mitchell 1990, 1996)','sigma_v':'1','alpha_water':'2','delta_a2':'1.88','delta_a1':'1.88','delta_v2':'1.80','g_water':'1','sigma_a':'0.5201','Dr':'79'},
{'g_ice':'1','alpha_ice':'4','delta_v1':'2.42','psettype':'Broad Branched Crystal (Mitchell 1990, 1996)','sigma_v':'0.0988','alpha_water':'2','delta_a2':'1.76','delta_a1':'1.85','delta_v2':'2.02','g_water':'1','sigma_a':'0.8075','Dr':'100'}
]

    ret="""
var datasetpath='%i';
var jspath='site';
var psetKeys_arr = new Array(%s);
var locationelement='site=%i';
var psets=new Array(
{g_ice:'1',alpha_ice:'4',delta_v1:'3',psettype:'Solid Spheres',sigma_v:'1',alpha_water:'2',delta_a2:'2',delta_a1:'2',delta_v2:'3',g_water:'1',sigma_a:'1',Dr:'100'},
{g_ice:'1',alpha_ice:'4',delta_v1:'3',psettype:'Fire II (Arnott 1994)',sigma_v:'0.266',alpha_water:'2',delta_a2:'1.27',delta_a1:'2',delta_v2:'2.26',g_water:'1',sigma_a:'0.76',Dr:'200'},
{g_ice:'1',alpha_ice:'4',delta_v1:'2.91',psettype:'Hex Columns (Mitchell 1996)',sigma_v:'0.485',alpha_water:'2',delta_a2:'1.5',delta_a1:'2',delta_v2:'1.91',g_water:'1',sigma_a:'0.87',Dr:'100'},
{g_ice:'1',alpha_ice:'4',delta_v1:'3',psettype:'Bullet Rosettes (Mitchell 1996)',sigma_v:'0.26',alpha_water:'2',g_water:'1',isdefault:'yes',delta_a1:'2',delta_v2:'2.26',delta_a2:'1.57',sigma_a:'1.0',Dr:'60'},
{g_ice:'1',alpha_ice:'4',delta_v1:'2.42',psettype:'Stellar Crystal (Mitchell 1996)',sigma_v:'0.2',alpha_water:'2',delta_a2:'1.63',delta_a1:'1.85',delta_v2:'1.67',g_water:'1',sigma_a:'0.7',Dr:'90'},
{g_ice:'1',alpha_ice:'4',delta_v1:'3',psettype:'Aggregates of Thin Plates (Mitchell 1990, 1996)',sigma_v:'1',alpha_water:'2',delta_a2:'1.88',delta_a1:'1.88',delta_v2:'1.80',g_water:'1',sigma_a:'0.5201',Dr:'79'},
{g_ice:'1',alpha_ice:'4',delta_v1:'2.42',psettype:'Broad Branched Crystal (Mitchell 1990, 1996)',sigma_v:'0.0988',alpha_water:'2',delta_a2:'1.76',delta_a1:'1.85',delta_v2:'2.02',g_water:'1',sigma_a:'0.8075',Dr:'100'});


function psetKeys() {
return psetKeys_arr;
}

function sanityCheckSubmit() {
  itemlist=document.forms['reqform'];
  var idxname = itemlist['filemode'].value;
  var uname = itemlist['username'];
  var invcount=0;
  if(idxname!='single' && uname.value.length<4){
     invcount++;
     document.getElementById('fm_multi').style.backgroundColor='#ffaaaa';
  }else{
     document.getElementById('fm_multi').style.backgroundColor='';
  }
  var sbmt=null;
  for(i=0;i<itemlist.length;i++){
     var tempobj = itemlist.elements[i];
     if (tempobj.type.toLowerCase() == "submit")
       sbmt=tempobj;
  }

  try{
  if(idxname=='routine' && itemlist['sat_timeslist'].value==''){
    document.getElementById('sat_times_hi').style.backgroundColor='#ffaaaa';
    invcount++;
  }else{
    document.getElementById('sat_times_hi').style.backgroundColor='';
  }
  }catch(e){}
    
  try{
  if(idxname=='satellite' && parseInt(document.getElementById("overpasscount").innerHTML)<=0){ //.split(' ')[0])<=0)
    invcount++;
    document.getElementById("overpasscount_hi").style.backgroundColor='#ffaaaa';
    document.getElementById("overpasscount").style.color='#aa0000';
  }else{
    document.getElementById("overpasscount_hi").style.backgroundColor='';
    document.getElementById("overpasscount").style.color='';
  }
  }catch(e){}
  if(itemlist['custom_display']!=null && itemlist['custom_display'].checked && itemlist['display_defaults_content'].value=="")
    invcount++;
  if(itemlist['custom_processing']!=null && itemlist['custom_processing'].checked && itemlist['process_parameters_content'].value=="")
    invcount++;
  if(itemlist['cdltemplatename'].value=='custom' && itemlist['cdltemplate_content'].value=="")
    invcount++;

  if(invcount>0){
    sbmt.disabled=true;
  }else{
    sbmt.disabled=false;
  }
}

function updateTemplateVisibility(){
  if(itemlist['cdltemplatename'].value=='custom')
    document.getElementById("cdltemplate_custom").style.display=""
  else
    document.getElementById("cdltemplate_custom").style.display="none"
}

var fallbackTimeout=false;

function rebuildSatTimes(){
  itemlist=document.forms['reqform'];
  timelist=itemlist['sat_times'];
  ttlist=itemlist['sat_timeslist'];
  slist='';
  if(timelist.options.length>0)
     slist=String(timelist.options[0].value);
  for(i=1;i<timelist.options.length;i++){
     slist+=" " + String(timelist.options[i].value);
  }
  ttlist.value=slist;
  sanityCheckSubmit();
}

function addSatTime(){
  itemlist=document.forms['reqform'];
  timelist=itemlist['sat_times'];
  ht=itemlist['sat_hour'];
  mt=itemlist['sat_min'];
  var o=new Option(ht.value+':'+mt.value,parseFloat(ht.value)*60+parseFloat(mt.value),false,false);
  for(i=0;i<timelist.options.length;i++){
    if(timelist.options[i].value==o.value){
      return;
    }
    if(parseFloat(timelist.options[i].value)>parseFloat(o.value)){
       tmp=timelist.options[i];
       timelist.options[i]=o;
       o=tmp       
    }
  }
  timelist.options[timelist.options.length]=o;
  rebuildSatTimes();
}

function remSatTime(){
  itemlist=document.forms['reqform'];
  timelist=itemlist['sat_times'];
  for(i=timelist.options.length-1;i>=0;i--)
    if(timelist.options[i].selected)
      timelist.options[i]=null;
  rebuildSatTimes();
  itemlist['sat_rem'].disabled=true;
}

function updateFMVisibilities() {
  itemlist=document.forms['reqform'];
  va=document.getElementById('fm_multi');
  ohm=document.getElementById('overhead_mins');
  sat=document.getElementById('satelliteselect');
  clk=document.getElementById('overhead_times');
  sr=itemlist['sat_rem'];
  remidx=itemlist['sat_times'];
  var idx = itemlist['filemode'].selectedIndex;
  if(idx==0){
    va.style.display="none";
  }else{
    va.style.display="";
  }
  if(sat!=null)
    sat.style.display="none";
  if(ohm!=null)
    ohm.style.display="none";
  if(clk!=null)
    clk.style.display="none";
  if(idx==1 && sat!=null && ohm!=null){
    sat.style.display="";
    ohm.style.display="";
  }else if((idx==2 && clk!=null && ohm!=null) || (idx==1 && clk!=null && ohm!=null && sat==null)){
    clk.style.display="";
    ohm.style.display="";
  }
  if(sr!=null){
  if(remidx==null || remidx.selectedIndex<0)
    sr.disabled=true;
  else
    sr.disabled=false;
  }
}

function r2bscsUpdate(){
return;//FIXME
  itemlist = document.forms['reqform'];
  var lambda_radar=8.6e-3;
  var k_water_sq=0.92;  
  var k_sq_ice=0.197;

  var radar_constant=Math.pow(Math.PI,5)*k_water_sq/(4*Math.PI*Math.pow(lambda_radar,4));
  radar_constant=radar_constant*1e-18;
  var ref=parseFloat(itemlist['qc_params.min_radar_dBz'].value)
  if(isNaN(ref)){
    itemlist['qc_params.min_radar_dBz'].value='';
    itemlist['qc_params.min_radar_backscat'].value='';
  }else{
    itemlist['qc_params.min_radar_backscat'].value=String((radar_constant*Math.pow(10,(ref)/10)).toPrecision(3));
  }
}

function bscs2rUpdate(){
return;//FIXME
  itemlist = document.forms['reqform'];
  var lambda_radar=8.6e-3;
  var k_water_sq=0.92;  
  var k_sq_ice=0.197;

  var radar_constant=Math.pow(Math.PI,5)*k_water_sq/(4*Math.PI*Math.pow(lambda_radar,4));
  radar_constant=radar_constant*1e-18;
  var bscat=parseFloat(itemlist['qc_params.min_radar_backscat'].value)
  if(isNaN(bscat)){
    itemlist['qc_params.min_radar_dBz'].value='';
    itemlist['qc_params.min_radar_backscat'].value='';
  }else{
    itemlist['qc_params.min_radar_dBz'].value=String(((Math.log(bscat/radar_constant)/Math.LN10)*10).toFixed(1));
  }
}

function clearPSET() {
  itemlist = document.forms['reqform'];
  itemlist['presetPSET'].selectedIndex=0;
  itemlist['particlesettings.psettype'].value='custom';
}

function changePSET() {
  itemlist = document.forms['reqform'];
  try{
  idx=itemlist['presetPSET'].selectedIndex;
  if (idx<=0)
    return;
  idx=idx-1;
  var keys=psetKeys();
  if(idx>=psets.length)
    return;
  var pset=psets[idx];
  var i=0;
  prefix='particlesettings.';

  for(i=0;i<keys.length;i++)
    if(keys[i] in pset)
      if(itemlist[prefix+keys[i]]!=null)
        itemlist[prefix+keys[i]].value=pset[keys[i]];
  }catch(e){}
}

var xmlhttps=new Array(false,false);

function getReq(idx){
  xmlhttp=xmlhttps[idx];
 //window.console.log('req #' + String(idx) + ' is ' + xmlhttp)
if(xmlhttp){
  xmlhttp.abort();
  //window.console.log('res are equal? ' + (xmlhttps[0]==xmlhttps[1])) 
  return xmlhttp;
}
 try {
  xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
 } catch (e) {
  try {
   xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
  } catch (E) {
   xmlhttp = false;
  }
 }
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
xmlhttps[idx]=xmlhttp;
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

function doDisable(objs,field,disable,checkval){
  try{
  obj=objs[field];
  wasDis=obj.disabled;
  }catch(e){return;}
  if(disable==wasDis)
    return;
  if(disable){
    obj.disabled=true;
    if (obj.type.toLowerCase() == "checkbox"){
      enState[field]=obj.checked;
      obj.checked=checkval;
    }
  }else{
    obj.disabled=false;
    if (obj.type.toLowerCase() == "checkbox"){
      obj.checked=enState[field];
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

function beginSatUpdating(){
progressdisplay=document.getElementById('overpass_progress');
progressdisplay.style.display="";
}

function finishSatUpdating(){
progressdisplay=document.getElementById('overpass_progress');
progressdisplay.style.display="none";
}

var needany=new Array('RdoProf');
var needlidar=new Array('PartBackXSec','Cmb','PartOptDep','Mol','PartDepol','Crs','PartScatXSec','AttenBackScat','MolScatXSec','ErrEst','System','qc_params.mol_lost','qc_params.mol_snr','qc_params.backscat_snr','qc_params.lock_level','qc_params.min_beta_a');
var needmerge=new Array('Reflec','RdBackscat','SpectralWid','DopplerVelocity','qc_params.min_radar_backscat','qc_params.min_radar_dBz');
var needrig=new Array('RIG');
var needmwr=new Array('MWR_BT','MWR_PATH');
var needpaeri0=new Array('AERI_BT');
var needpaeri1=new Array('AERI_RAD');
var needpaeripca1=new Array('AERI_PCA_RAD');
var needlidaramerge=new Array('EffectiveDiameterPrime','ParticleMeasurements');

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

function updateDeltas() {
  itemlist = document.forms['reqform'];
  itemlist['delta_v2'].value=itemlist['particlesettings.delta_v'].value;
  itemlist['delta_a2'].value=itemlist['particlesettings.delta_a'].value;
}


function updateVisibilities() {
  itemlist=document.forms['reqform'];
  edp=document.getElementById('param_edp_part');
  part=document.getElementById('param_part');
  sg=document.getElementById('showgraph');
  if(sg!=null)
    sg.style.display="";

  try{
  if(itemlist['ParticleMeasurements'].checked ||
     itemlist['EffectiveDiameterPrime'].checked)
    edp.style.display="";
  else
    edp.style.display="none";
    }catch(e){
    if(edp!=null)
     edp.style.display="none";
    }
    try{
  if(itemlist['ParticleMeasurements'].checked)
    part.style.display="";
  else
    part.style.display="none";
    }catch(e){
    if(part!=null)
    part.style.display="none";
    }
  if(itemlist['custom_processing']!=null){
    if (itemlist['custom_processing'].checked)
      document.getElementById('custom_processing_field').style.display='';
    else
      document.getElementById('custom_processing_field').style.display='none';
  }
  if(itemlist['custom_display']!=null){
    if(itemlist['custom_display'].checked)
      document.getElementById('custom_display_field').style.display='';
    else
      document.getElementById('custom_display_field').style.display='none';
  }
}


function toggleCheckbox(name){
  var itemlist = document.forms['reqform'];
  var cb=itemlist[name];
  if(!cb.disabled){
    cb.checked=!cb.checked;
  }
}

function gridsizereasonable(){
  var itemlist = document.forms['reqform'];
  var timelen=0;
  fm=itemlist['filemode'].value;
  if(fm=='single'){
    var btstr=itemlist['byr'].value + '/' + padString(String(itemlist['bmo'].selectedIndex+1),'0',2) + '/' + padString(itemlist['bdy'].value,'0',2)  + ' ' + padString(itemlist['bhr'].value,'0',2) + ':' + padString(itemlist['bmn'].value,'0',2);
    var etstr=itemlist['eyr'].value + '/' + padString(String(itemlist['emo'].selectedIndex+1),'0',2) + '/' + padString(itemlist['edy'].value,'0',2)  + ' ' + padString(itemlist['ehr'].value,'0',2) + ':' + padString(itemlist['emn'].value,'0',2);
    timelen=(Date.parse(etstr) - Date.parse(btstr))/1000;
    //window.console.log(etstr + ' - ' + btstr + ' = ' + String(timelen));
  }else if(fm=='30minute'){
    timelen=30*60;
  }else if(fm=='hour'){
    timelen=60*60;
  }else if(fm=='day'){
    timelen=24*60*60;
  }else if(fm=='week'){
    timelen=7*24*60*60;
  }else if(fm=='month'){
    timelen=30*24*60*60;
  }else{
    return true;
  }
  var gridsize=(parseFloat(itemlist['height'].value)-parseFloat(itemlist['lheight'].value))/(parseFloat(itemlist['altres'].value)/1000.0 + 1)*(timelen/parseFloat(itemlist['timeres'].value)+1);
  var gridsizelimit=300000;//24*60*60*15000/(5*30);
  window.console.log('estimated Gridsize ' + String(gridsize) + ' vs limit of ' + String(gridsizelimit) + ' values per RTI variable');
  return Boolean(gridsize<gridsizelimit)
}

function checkGridSize(){
  reasonable=document.getElementById('filemoderecommend');
  if(gridsizereasonable()){
    reasonable.style.display="none";
  }else{
    reasonable.style.display="";
  }
}

function checkOverpassCount(){
  var itemlist = document.forms['reqform'];
  if(itemlist['filemode'].value!='satellite'){
    sanityCheckSubmit();
    return;
  }
  beginSatUpdating();
  var bstr=itemlist['byr'].value + padString(String(itemlist['bmo'].selectedIndex+1),'0',2) + padString(itemlist['bdy'].value,'0',2)  + 'T' + padString(itemlist['bhr'].value,'0',2) + padString(itemlist['bmn'].value,'0',2);
  var estr=itemlist['eyr'].value + padString(String(itemlist['emo'].selectedIndex+1),'0',2) + padString(itemlist['edy'].value,'0',2)  + 'T' + padString(itemlist['ehr'].value,'0',2) + padString(itemlist['emn'].value,'0',2);
  var availurl='http://lidar.ssec.wisc.edu/cgi-bin/util/overpassCount?' + locationelement + '&time0='+bstr+'&time1='+estr+'&satellite='+ itemlist['satellite'].value + '&maxdist=' +  itemlist['sat_maxdist'].value ;
  var r=getReq(1);
  r.open('GET',availurl,true);
  r.onreadystatechange=function(){
    if(r.readyState!=4)
      return;
    var count=r.responseText;
    //window.console.log('got count check of ' + count)
    document.getElementById("overpasscount").innerHTML=count;
    var ico=parseInt(count);
    if (ico<=0)
      itemlist['satlist'].disabled=true;
    else
      itemlist['satlist'].disabled=false;
    sanityCheckSubmit();
    finishSatUpdating();
  }
  r.send(null);
  
  //window.console.log('submit overpass count check');
}

function checkDataAvailability(enabled) {
  checkGridSize();  checkOverpassCount();
  var itemlist = document.forms['reqform'];
  beginUpdating();
  //var dbg=itemlist['DEBUG'];
  var bstr=itemlist['byr'].value + padString(String(itemlist['bmo'].selectedIndex+1),'0',2) + padString(itemlist['bdy'].value,'0',2)  + 'T' + padString(itemlist['bhr'].value,'0',2) + padString(itemlist['bmn'].value,'0',2);
  var estr=itemlist['eyr'].value + padString(String(itemlist['emo'].selectedIndex+1),'0',2) + padString(itemlist['edy'].value,'0',2)  + 'T' + padString(itemlist['ehr'].value,'0',2) + padString(itemlist['emn'].value,'0',2);
  var availurl='%s?'+jspath+'='+datasetpath+'&time0='+bstr+'&time1='+estr;
  //dbg.value=availurl;
  var r=getReq(0);
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

function previewSatList(){
  if (parseInt(document.getElementById("overpasscount").innerHTML)<=0)
    return;
  var bstr=itemlist['byr'].value + padString(String(itemlist['bmo'].selectedIndex+1),'0',2) + padString(itemlist['bdy'].value,'0',2)  + 'T' + padString(itemlist['bhr'].value,'0',2) + padString(itemlist['bmn'].value,'0',2);
  var estr=itemlist['eyr'].value + padString(String(itemlist['emo'].selectedIndex+1),'0',2) + padString(itemlist['edy'].value,'0',2)  + 'T' + padString(itemlist['ehr'].value,'0',2) + padString(itemlist['emn'].value,'0',2);
  var availurl='http://lidar.ssec.wisc.edu/cgi-bin/util/overpassList?' + locationelement + '&time0='+bstr+'&time1='+estr+'&satellite='+ itemlist['satellite'].value + '&maxdist=' +  itemlist['sat_maxdist'].value ;
  window.open(availurl,"SatOverpassPreview");
}


function showCustomEmail(){
  es=document.getElementById('emailset');
  es.style.display="none";
  ec=document.getElementById('emailcustom');
  ec.style.display="";
}
    """ % (pathidx,"'" + "','".join(psetKeys) + "'",pathidx,makeUpdateFromData(formsetsForInstruments(instruments,'netcdf')),dataAvailabilityPath)
    return ret

def imagejavascriptgen(pathidx,instruments,dataAvailabilityPath):
 
    ret="""
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
  var itemlist = document.forms['reqform'];
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
  itemlist=document.forms['reqform'];
  var invcount=0;
  var sbmt=null;
  for(i=0;i<itemlist.length;i++){
     var tempobj = itemlist.elements[i];
     if (tempobj.type.toLowerCase() == "submit")
       sbmt=tempobj;
  }

  if(itemlist['custom_display']!=null && itemlist['custom_display'].checked && itemlist['display_defaults_content'].value=="")
    invcount++;
  if(itemlist['custom_processing']!=null && itemlist['custom_processing'].checked && itemlist['process_parameters_content'].value=="")
    invcount++;


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
  var itemlist = document.forms['reqform'];
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
  var itemlist = document.forms['reqform'];
  var cb=itemlist[name];
  for(i=0;i<cb.length;i++)
    if(cb[i].value==value){
      if(!cb[i].disabled)
        cb[i].checked=true;
      break;
    }
}

function toggleCheckbox(name){
  var itemlist = document.forms['reqform'];
  var cb=itemlist[name];
  if(!cb.disabled){
    cb.checked=!cb.checked;
  }
}

function updateVisibilities() {
  itemlist=document.forms['reqform'];
  if(itemlist['custom_display']!=null){
  if(itemlist['custom_display'].checked)
    document.getElementById('custom_display_field').style.display='';
  else
    document.getElementById('custom_display_field').style.display='none';
  }
  if(itemlist['custom_processing']!=null){
  if(itemlist['custom_processing'].checked)
    document.getElementById('custom_processing_field').style.display='';
  else
    document.getElementById('custom_processing_field').style.display='none';
  }
}

function showCustomEmail(){
  es=document.getElementById('emailset');
  es.style.display="none";
  ec=document.getElementById('emailcustom');
  ec.style.display="";
}
""" % (pathidx,makeUpdateFromData(formsetsForInstruments(instruments,'images')),dataAvailabilityPath)
    return ret


if __name__ == '__main__':
    print makeUpdateFromData(formsetsForInstruments(['lidar','radiosonde','baseline','merge','paeri0'],'images'))

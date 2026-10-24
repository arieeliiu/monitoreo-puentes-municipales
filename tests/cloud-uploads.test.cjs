const {test}=require('node:test');
const assert=require('node:assert/strict');
const {readFileSync}=require('node:fs');
const {resolve}=require('node:path');
const {runInNewContext}=require('node:vm');
const script=readFileSync(resolve(__dirname,'../static/cloud-uploads.js'),'utf8');

function fixture(files,fetcher){
  let submit;
  const file={files,disabled:false};
  const button={textContent:'Guardar inspección',disabled:false};
  const children=[];
  const form={enctype:'multipart/form-data',submitted:0,
    addEventListener:(_,fn)=>{submit=fn;},
    append:node=>children.push(node),
    requestSubmit(){this.submitted++;},
    querySelector(selector){
      if(selector==='input[name=photos]')return file;
      if(selector.startsWith('button'))return button;
      if(selector==='[name=csrf]')return {value:'session-csrf'};
      if(selector==='[name=staged_uploads]')return children.find(c=>c.name==='staged_uploads');
      if(selector==='[data-upload-error]')return children.find(c=>c.dataset.uploadError==='');
      throw Error('Selector no cubierto: '+selector);
    }};
  const document={querySelectorAll:()=>[form],createElement:tag=>({tag,dataset:{},setAttribute(){}})};
  runInNewContext(script,{document,fetch:fetcher,URLSearchParams});
  return {form,file,button,children,submit:()=>submit({preventDefault(){}})};
}

test('rechaza más de 20 MB antes de subir y conserva el formulario',async()=>{
  let calls=0;const f=fixture([{size:21*1024*1024}],async()=>{calls++;});
  await f.submit();assert.equal(calls,0);assert.equal(f.form.submitted,0);assert.equal(f.button.disabled,false);
  assert.match(f.children[0].textContent,/20 MB/);
});
test('sube directamente con token temporal y envía solo el manifiesto al backend',async()=>{
  const calls=[];
  const f=fixture([{size:6*1024*1024,type:'image/png'}],async(url,options)=>{
    calls.push({url,options});
    return calls.length===1?{ok:true,json:async()=>({uploads:[{name:'authorized.upload',url:'https://storage.example/upload?token=temporary'}]})}:{ok:true};
  });
  await f.submit();assert.equal(calls.length,2);
  assert.equal(calls[0].url,'/uploads/prepare');assert.equal(calls[0].options.body.get('csrf'),'session-csrf');
  assert.equal(calls[1].options.method,'PUT');assert.equal(calls[1].options.credentials,'omit');
  assert.equal(calls[1].options.headers.apikey,undefined);
  assert.equal(f.file.disabled,true);assert.equal(f.form.enctype,'application/x-www-form-urlencoded');assert.equal(f.form.submitted,1);
  assert.equal(f.children.find(c=>c.name==='staged_uploads').value,'["authorized.upload"]');
});
test('un fallo de Storage conserva los archivos y habilita reintentar',async()=>{
  let calls=0;const f=fixture([{size:200,type:'image/jpeg'}],async()=>++calls===1?{ok:true,json:async()=>({uploads:[{name:'x',url:'https://storage.example/x'}]})}:{ok:false});
  await f.submit();assert.equal(f.form.submitted,0);assert.equal(f.file.disabled,false);assert.equal(f.button.disabled,false);
  assert.match(f.children[0].textContent,/Intenta nuevamente/);
});
test('una inspección sin fotos conserva el envío nativo',async()=>{
  const f=fixture([],async()=>{throw Error('No debe llamar Storage');});await f.submit();assert.equal(f.file.disabled,false);
});

document.querySelectorAll('form[data-cloud-photos]').forEach(form=>{
  let ready=false;
  form.addEventListener('submit',async event=>{
    const field=form.querySelector('input[name=photos]');
    if(ready || !field.files.length)return;
    event.preventDefault();
    const button=form.querySelector('button[type=submit],button');
    const original=button.textContent;button.disabled=true;button.textContent='Guardando fotografías…';
    let notice=form.querySelector('[data-upload-error]');
    if(!notice){notice=document.createElement('p');notice.dataset.uploadError='';notice.setAttribute('role','alert');form.append(notice);}
    notice.textContent='';
    try{
      const files=Array.from(field.files);
      if(files.length>5 || files.reduce((n,f)=>n+f.size,0)>20*1024*1024)throw Error('Adjunta hasta 5 fotografías, con un total máximo de 20 MB.');
      const payload=new URLSearchParams({csrf:form.querySelector('[name=csrf]').value,files:JSON.stringify(files.map(f=>({size:f.size})))});
      const response=await fetch('/uploads/prepare',{method:'POST',body:payload});
      const result=await response.json();if(!response.ok)throw Error(result.error || 'No fue posible preparar las fotografías.');
      for(let i=0;i<files.length;i++){
        const uploaded=await fetch(result.uploads[i].url,{method:'PUT',headers:{'Content-Type':files[i].type || 'image/jpeg'},body:files[i],credentials:'omit'});
        if(!uploaded.ok)throw Error('No fue posible subir una fotografía. Intenta nuevamente.');
      }
      let manifest=form.querySelector('[name=staged_uploads]');
      if(!manifest){manifest=document.createElement('input');manifest.type='hidden';manifest.name='staged_uploads';form.append(manifest);}
      manifest.value=JSON.stringify(result.uploads.map(u=>u.name));
      field.disabled=true;ready=true;form.enctype='application/x-www-form-urlencoded';
      form.requestSubmit();
    }catch(error){notice.textContent=error.message;button.disabled=false;button.textContent=original;}
  });
});

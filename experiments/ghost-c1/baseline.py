"""Rebuild exact cf0ef00 sources in an isolated comparison tree."""
import subprocess,pathlib,tarfile,io,shutil,json,hashlib
from bindings import ROOT,OUT
ref=OUT/'reference';ref.mkdir(exist_ok=True)
commit=subprocess.check_output(['git','rev-parse','cf0ef00^{commit}'],cwd=ROOT,text=True).strip()
archive=subprocess.check_output(['git','archive',commit],cwd=ROOT)
with tarfile.open(fileobj=io.BytesIO(archive)) as t:t.extractall(ref,filter='data')
(ref/'build').mkdir(exist_ok=True)
for file in ['params.h','factory.h']:shutil.copy2(ROOT/'build'/file,ref/'build'/file)
products=OUT/'reference-products';products.mkdir(exist_ok=True)
subprocess.run(['make','-C',str(ref/'experiments/ghost-c1'),'OUT='+str(products),'all','vst'],check=True)
subprocess.run(['make','-C',str(ref/'experiments/ghost-c1'),'OUT='+str(products),str(products/'vst-benchmark')],check=True)
with (OUT/'benchmark-C1-reference.csv').open('w') as f:subprocess.run([str(products/'vst-benchmark'),str(products/'beatrepeat-ghost-c1.so')],stdout=f,check=True)
manifest={'commit':commit,'files':{str(p.relative_to(ref)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ref/'experiments/ghost-c1').iterdir() if p.is_file()},'vst_sha256':hashlib.sha256((products/'beatrepeat-ghost-c1.so').read_bytes()).hexdigest()}
(OUT/'C1-reference.json').write_text(json.dumps(manifest,indent=2))

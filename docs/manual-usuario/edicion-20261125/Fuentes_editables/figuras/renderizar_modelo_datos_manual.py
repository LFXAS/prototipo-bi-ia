"""Exportación de gráficos por CLI; sin interfaz ni llamadas a la aplicación."""
from pathlib import Path
import subprocess,json,hashlib,argparse
from PIL import Image
W=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--only',action='append',default=[]);args=ap.parse_args()
items=json.loads((W/'manifest_figuras_datos.json').read_text());processed=0
for r in items:
 if args.only and Path(r['archivo_svg']).stem not in args.only:continue
 processed+=1
 svg=W/r['archivo_svg'];pdf=svg.with_suffix('.pdf');png=svg.with_suffix('.png')
 p=subprocess.run(['/usr/bin/inkscape',str(svg),'--export-area-page','--export-type=pdf','--export-filename='+str(pdf)],capture_output=True,text=True)
 assert p.returncode==0,p.stderr
 subprocess.run(['/home/ceo/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm','-singlefile','-scale-to-x','2717','-scale-to-y','1449','-png',str(pdf),str(png.with_suffix(''))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 with Image.open(png) as im:im.convert('RGB').save(png,dpi=(300,300))
 r['archivo_pdf']=pdf.name;r['png_dimensiones_px']=[2717,1449];r['png_rgb']=True
 for ext in ['svg','png','pdf']:r['sha256_'+ext]=hashlib.sha256(svg.with_suffix('.'+ext).read_bytes()).hexdigest()
(W/'manifest_figuras_datos.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
print(str(processed)+' SVG/PDF vectoriales/PNG RGB a 300 dpi exportados.')

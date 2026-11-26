import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const require=createRequire('/home/ceo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json');
const sharp=require('sharp');
const root=dirname(fileURLToPath(import.meta.url));
for(const stem of ['Arquitectura_detallada_BI_IA','Arquitectura_general_BI_IA']){
 await sharp(join(root,stem+'.svg'),{density:144}).resize({width:2400}).png().toFile(join(root,stem+'.png'));
}

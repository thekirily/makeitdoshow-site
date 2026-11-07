#!/usr/bin/env node
// Check every HTML route, including orphan/noindex pages, with staging-origin rewrites explicit.
import {LinkChecker} from 'linkinator';
import {readFile,writeFile,readdir} from 'node:fs/promises';
import {resolve,relative,join} from 'node:path';
const [rootArg='.',base='http://127.0.0.1:8115',phase='after',internal='']=process.argv.slice(2);
const root=resolve(rootArg), files=[];
async function walk(dir){for(const e of await readdir(dir,{withFileTypes:true})){if(['node_modules','evidence','.git','.playwright-mcp'].includes(e.name))continue;const p=join(dir,e.name);if(e.isDirectory())await walk(p);else if(p.endsWith('.html'))files.push(p);}}
await walk(root);
const paths=files.map(f=>base+'/'+relative(root,f).replace(/index\.html$/,''));
const output={instrument:'linkinator 8.1.0',scope:'All HTML routes; canonical same-site origins rewritten to branch preview. Public-origin failures remain in separate raw live scan. HTTP assertions do not certify external content accuracy.',profiles:[]};
for(const device of ['mobile','desktop']){
 const checker=new LinkChecker();
 const result=await checker.check({path:paths,recurse:false,concurrency:4,timeout:25000,checkFragments:true,checkCss:true,retry:false,retryErrors:false,userAgent:device==='mobile'?'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/132.0 Mobile Safari/537.36':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/132.0 Safari/537.36',urlRewriteExpressions:[{pattern:/^https:\/\/makeitdoshow\.com(?=\/)/,replacement:base}],linksToSkip:internal?async url=>!url.startsWith(base+'/'):undefined});
 output.profiles.push({device,html_routes:paths.length,...result});
 await writeFile(`evidence/launch-1107/${phase}-links-all.json`,JSON.stringify(output,null,2)+'\n');
 console.log(device,paths.length,'routes',result.links.length,'references',result.links.filter(l=>l.state==='BROKEN').length,'failures');
}
process.exitCode=output.profiles.some(p=>!p.passed)?1:0;

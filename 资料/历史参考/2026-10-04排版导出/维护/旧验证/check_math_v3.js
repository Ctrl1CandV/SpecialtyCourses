const fs=require('fs'),path=require('path');
const katex=require('D:/Program Project/SpecialtyCourses/_tmp/pdf_build_optimized/katex/dist/katex.min.js');
const v3=JSON.parse(fs.readFileSync('D:/Program Project/SpecialtyCourses/_tmp/pdf_v3/math_nodes_v3.json','utf8'));
const base=JSON.parse(fs.readFileSync('D:/Program Project/SpecialtyCourses/_tmp/pdf_build_optimized/math_nodes.json','utf8'));
const fail=xs=>xs.filter(x=>{try{katex.renderToString(x,{throwOnError:true,strict:false});return false;}catch(e){return true;}});
const result={};let bad=false;
for(const name of ['精选题集','补充题集','答案册']){
  const cur=fail(base[name+'_current']);      // 基线（上一轮优化版）已存在的错误
  const now=fail(v3[name+'_v3']);
  const added=now.filter(x=>!cur.includes(x));
  result[name]={v3Spans:v3[name+'_v3'].length,baseSpans:base[name+'_current'].length,
                baseErrors:cur.length,v3Errors:now.length,newErrors:added};
  if(added.length)bad=true;
}
fs.writeFileSync('D:/Program Project/SpecialtyCourses/_tmp/pdf_v3/math_verification_v3.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
if(bad)process.exitCode=1;

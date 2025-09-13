from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import io
import re
import os
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["https://essolution.dev", "https://www.essolution.dev"]}})
def apiHandler(key):
  apiKey = os.environ.get("API_KEY")
  print(apiKey, key)
  return apiKey==key
@app.route('/api/run', methods=['POST'])
def run():
  try:
    APIKEY = request.headers.get("x-api-key")
    if APIKEY is None:
      return jsonify({"message":"Error: Api key not found"}), 404
    if not apiHandler(APIKEY):
      return jsonify({"message": "Error: Invalid api key"}), 403
    pattern = r'(?:\b(\w+)\s*=\s*)?input\(\s*"?([\s\S]*?)"?\s*\)'
    regex = r'<input(?:-\b([\s\S]*?))?(?:-\b([\s\S]*?))?>'
    disgrex = r'print\(\s*?([\s\S]*?)\s*\)'
    degex = r'<output(?:-\b(\w+))?(?:-\b([\s\S]*?))?>'
    dgex = r'["]'
    sgex = r"[']"
    def replace_input(match):
      id_name = match.group(1) or ""
      placeholder = match.group(2).strip() if match.group(2) else ""
      if(placeholder and id_name):
        return f'print("<input-{id_name}-{placeholder}>")'
      elif(placeholder): 
       return f'print("<input-{placeholder}>")'
      elif(id_name):
       return f'print("<input-{id_name}>")'
      else:
        return 'print("<input-none>")'
    def replace_regrex(match):
      id_name = match.group(1) or ""
      placeholder = match.group(2).strip() if match.group(2) else ""
      vname = re.findall(regex, result)
      print("input", vname)
      return f'<label for="{placeholder}">{placeholder}<input id="input-{id_name}-{placeholder}" type="text" size="30" style="border:none; background-color:transparent"/></label><script>const input_{id_name} = document.getElementById("input-{id_name}-{placeholder}"); input_{id_name}.addEventListener("focus", ()=>input_{id_name}.style.outline="none");window.onload=()=>input_{vname[0][0]}.focus()</script>' if placeholder else f'<input id="input-{"_".join(id_name.split())}" type="text" size="30" style="border:none; background-color:transparent"/><script>const input_{"_".join(id_name.split())} = document.getElementById("input-{"_".join(id_name.split())}"); input_{"_".join(id_name.split())}.addEventListener("focus", ()=>input_{"_".join(id_name.split())}.style.outline="none"); window.onload=()=>input_{"_".join(vname[0][0].split())}.focus()</script>'
    data = request.json
    result = re.sub(pattern, replace_input, data)
    result = re.sub(r'pip\s*install|pip\s*uninstall|\s*pip\s*', '', result)
    vname = re.findall(regex, result)
    pname = re.findall(disgrex, data)
    variables = list()
    out_data = list()
    for x in vname:
      variables.append(x[0])
      for y in range(len(pname)):
        if(x[0] in pname[y]):
          if pname[y] not in out_data:
           out_data.append(pname[y])
           if(x[0] == pname[y]):
            print("v1", x[0], y)
            print(pname[y])
            print(out_data)
            result = re.sub(r'print\((?![\'"])[^)]+\)',f"print('<output-{x[0]}{len(out_data)-1}>')",result, count=1)
           else:
            print("v2", x[0], y)
            if not pname[y].startswith(("'", '"')):
             result = re.sub(pname[y],f'"<output-{x[0]}{len(out_data)-1}>"',result, count=1)
            else:
             print("v3",x[0],y)
             result = re.sub(pname[y],f"print('<output-{x[0]}{len(out_data)-1}>')",result, count=1)
    print(vname, pname, out_data, variables)
    print(result)
    def replace_out(match):
      stm = match.group(1).strip() or ""
      print(stm)
      outdata = ""
      num = int(stm[-1])
      outdata = outdata + f'<output id="output-{stm}"></output>'
      out_list = out_data
      print(f'num = {num}')
      for x in vname:
          if x[0] == out_list[num]:
            outdata = outdata + f'<script>const output_{x[0]}{stm}=document.getElementById("output-{stm}"); window.addEventListener("keydown", (e)=>{{e.key==="Enter"&&input_{x[0]}.disabled="true";output_{x[0]}{stm}.textContent = e.key==="Enter"?input_{x[0]}.value:""}})</script>'
            break
          elif out_list[num].startswith('f"'):
            outdata = outdata + f"<script>const value{stm}='{re.sub(sgex,'&#39;',re.escape(out_list[num]))}'; const output_{x[0]}{stm}=document.getElementById('output-{stm}'); window.addEventListener('keydown', (e)=>{{e.key==='Enter'&&input_{x[0]}.disabled='true';output_{x[0]}{stm}.innerHTML = e.key==='Enter'?value{stm}.replace(/f[\"'](.*)[\"']/,(p,m)=>"+'{'
            for v in variables:
              outdata = outdata + f'm=m.replaceAll("{{{v}}}",input_{v}.value);' 
            outdata = outdata+'return m}):""})</script>'
            break
          elif out_list[num].startswith("f'"):
            outdata = outdata + f'<script>const value{stm}="{re.sub(dgex,"&#39;",re.escape(out_list[num]))}"; const output_{x[0]}{stm}=document.getElementById("output-{stm}"); window.addEventListener("keydown", (e)=>{{e.key==="Enter"&&input_{x[0]}.disabled="true";output_{x[0]}{stm}.innerHTML = e.key==="Enter"?value{stm}.replace(/f["\'](.*)["\']/,(p,m)=>'+'{'
            for v in variables:
              outdata = outdata + f'm=m.replaceAll("{{{v}}}",input_{v}.value);' 
            outdata = outdata+'return m}):""})</script>'
            break
          else:
            out_list[num]=re.sub(r'"', "\'",out_list[num])
            outdata = outdata + f'<script>const value{stm}="{re.escape(out_list[num])}"; const output_{x[0]}{stm}=document.getElementById("output-{stm}"); window.addEventListener("keydown", (e)=>output_{x[0]}{stm}.textContent = e.key==="Enter"?value{stm}.replace(/(.*)/,(p,m)=>'+'{const fas=m.split(",");'
            for v in variables:
             outdata = outdata + f"for(let x=0; x<=fas.length-1; x++){{if(!fas[x].match(/[\"'](.*)['\"]/g)){{if(fas[x].trim()==='{v}'){{fas[x]=input_{v}.value;input_{v}.disabled='true';}}}}}};"
            outdata = outdata+"m=fas.join(' ');m=m.replace(/[\"',]/g,'');"+'return m}):"")</script>'
            break
      return outdata
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    exec(result)
    sys.stdout = old_stdout  # Restore original stdout
    result = redirected_output.getvalue()
    print(result)
    captured_result = re.sub(regex, replace_regrex, result)
    captured_result = re.sub(degex, replace_out, captured_result)
    print(captured_result)
    return jsonify({"message": f"<h5 style='background-color:#abbaba;color:#000;padding: 5px'>Python 3.12.8</h5><p style='display:flex;gap:10px;flex-direction:column;background-color:#abbaba;color:#000;padding: 5px'>{captured_result}<script>const inputs=document.querySelectorAll('input');for(const input of inputs){{input.style.color ='#555';input.style.autocomplete='off';input.style.autocorrect='off';input.style.spellcheck='false';input.style.autocapitalize='off';input.addEventListener('blur',()=>{{if(input.id==='input-none'&&input.value.trim()){{input.disabled='true'}}}})}}</script></p>"}), 200
  except Exception as e:
     return jsonify({"message": f"<h5 style='background-color:#abbaba;color:#000;padding: 5px'>Python 3.12.8<h5><section style='background-color:#abbaba;color:#000;padding: 5px'><p>input method has limited capabilities on our platform.</p><p>You can only print your inputs.</p><p style='color:red'>Error: {e}</p></section>" if len(vname)>0 else f"<h5 style='background-color:#abbaba;color:#000;padding: 5px'>Python 3.12.8</h5> <section style='background-color:#abbaba;color:#000;padding: 5px'><p style='color:red'>Error: {e}</p></section>"}), 500
   

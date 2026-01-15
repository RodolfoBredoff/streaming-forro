# Crie o arquivo core/widgets.py
from django import forms
from django.conf import settings

class S3ImageWidget(forms.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer)
        
        # URL atual para mostrar o preview se já existir
        preview_html = ""
        if value:
            preview_html = f'<div style="margin:10px 0;"><img src="{value}" style="max-height:150px; border-radius:5px; border:1px solid #ccc;"></div>'

        html = f"""
        <div class="s3-direct-widget" style="margin-top:5px; padding:15px; border:1px solid #ddd; background:#f9f9f9; border-radius:5px;">
            {preview_html}
            <label style="font-weight:bold; display:block; margin-bottom:5px;">Selecione uma imagem (Upload Direto S3):</label>
            <div style="display:flex; gap:10px; align-items:center;">
                <input type="file" id="file_{name}" accept="image/*" style="border:1px solid #ccc; padding:5px;">
                <button type="button" class="button" style="background:#417690; color:white; padding:5px 10px; border:none; border-radius:4px; cursor:pointer;" onclick="uploadToS3_{name}()">⬆️ Enviar Agora</button>
            </div>
            
            <div id="progress_container_{name}" style="display:none; margin-top:10px; width:100%; background:#e0e0e0; border-radius:4px;">
                <div id="bar_{name}" style="height:20px; width:0%; background:#4caf50; border-radius:4px; text-align:center; color:white; font-size:12px; line-height:20px;">0%</div>
            </div>
            <p id="status_{name}" style="font-size:12px; margin-top:5px; color:#666;"></p>
        </div>

        <script>
        async function uploadToS3_{name}() {{
            const fileInput = document.getElementById('file_{name}');
            const urlInput = document.getElementById('{attrs["id"]}'); // O input original do Django
            const progressBar = document.getElementById('bar_{name}');
            const statusText = document.getElementById('status_{name}');
            const container = document.getElementById('progress_container_{name}');

            if (!fileInput.files.length) {{
                alert('Selecione um arquivo primeiro!');
                return;
            }}

            const file = fileInput.files[0];
            container.style.display = 'block';
            statusText.innerText = 'Iniciando autenticação...';

            try {{
                // 1. Obter URL Assinada
                const res = await fetch(`/api/get-presigned-url/?file_name=${{encodeURIComponent(file.name)}}&file_type=${{encodeURIComponent(file.type)}}`);
                if (!res.ok) throw new Error('Falha ao obter permissão');
                const data = await res.json();

                // 2. Preparar Upload
                const formData = new FormData();
                Object.keys(data.fields).forEach(key => formData.append(key, data.fields[key]));
                formData.append("file", file);

                // 3. Enviar para S3
                const xhr = new XMLHttpRequest();
                xhr.open("POST", data.url, true);

                xhr.upload.onprogress = (e) => {{
                    if (e.lengthComputable) {{
                        const percent = Math.round((e.loaded / e.total) * 100);
                        progressBar.style.width = percent + '%';
                        progressBar.innerText = percent + '%';
                        statusText.innerText = 'Enviando para Amazon S3...';
                    }}
                }};

                xhr.onload = () => {{
                    if (xhr.status === 204 || xhr.status === 200) {{
                        // SUCESSO!
                        const fullUrl = data.url + '/' + data.fields.key;
                        urlInput.value = fullUrl; // Preenche o campo do Django
                        statusText.innerHTML = '<b style="color:green">✅ Upload Concluído! Salve o formulário abaixo.</b>';
                        
                        // Atualiza preview se possível
                        const existingPreview = document.querySelector('.s3-direct-widget img');
                        if(existingPreview) existingPreview.src = fullUrl;
                    }} else {{
                        statusText.innerText = '❌ Erro no upload: ' + xhr.status;
                    }}
                }};

                xhr.send(formData);

            }} catch (err) {{
                console.error(err);
                statusText.innerText = 'Erro: ' + err.message;
            }}
        }}
        </script>
        """
        return output + html
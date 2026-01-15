# Crie o arquivo core/widgets.py
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe

class S3ImageWidget(forms.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer)
        
        # URL atual para mostrar o preview se já existir
        preview_html = ""
        if value:
            preview_html = f'<div style="margin:10px 0;"><img src="{value}" style="max-height:150px; border-radius:5px; border:1px solid #ccc;"></div>'

        # HTML do Botão e Scripts
        html = f"""
        <div class="s3-direct-widget" style="margin-top:5px; padding:15px; border:1px solid #ddd; background:#f9f9f9; border-radius:5px;">
            {preview_html}
            <label style="font-weight:bold; display:block; margin-bottom:5px;">Selecione uma imagem (Upload para {settings.AWS_S3_CUSTOM_DOMAIN}):</label>
            <div style="display:flex; gap:10px; align-items:center;">
                <input type="file" id="file_{name}" accept="image/*" style="border:1px solid #ccc; padding:5px;">
                <button type="button" class="button" style="background:#417690; color:white; padding:5px 10px; border:none; border-radius:4px; cursor:pointer;" onclick="uploadToS3_{name}()">⬆️ Enviar e Salvar</button>
            </div>
            
            <div id="progress_container_{name}" style="display:none; margin-top:10px; width:100%; background:#e0e0e0; border-radius:4px;">
                <div id="bar_{name}" style="height:20px; width:0%; background:#4caf50; border-radius:4px; text-align:center; color:white; font-size:12px; line-height:20px;">0%</div>
            </div>
            <p id="status_{name}" style="font-size:12px; margin-top:5px; color:#666;"></p>
        </div>

        <script>
        async function uploadToS3_{name}() {{
            const fileInput = document.getElementById('file_{name}');
            const urlInput = document.getElementById('{attrs["id"]}');
            const progressBar = document.getElementById('bar_{name}');
            const statusText = document.getElementById('status_{name}');
            const container = document.getElementById('progress_container_{name}');

            if (!fileInput.files.length) {{
                alert('Selecione uma imagem primeiro!');
                return;
            }}

            const file = fileInput.files[0];
            container.style.display = 'block';
            statusText.innerText = 'Preparando envio...';

            try {{
                // 1. Pede a URL assinada (Agora vem com a pasta certa!)
                const res = await fetch(`/api/get-presigned-url/?file_name=${{encodeURIComponent(file.name)}}&file_type=${{encodeURIComponent(file.type)}}`);
                if (!res.ok) throw new Error('Erro na API');
                const data = await res.json();

                // 2. Upload para S3
                const formData = new FormData();
                Object.keys(data.fields).forEach(key => formData.append(key, data.fields[key]));
                formData.append("file", file);

                const xhr = new XMLHttpRequest();
                xhr.open("POST", data.url, true);

                xhr.upload.onprogress = (e) => {{
                    if (e.lengthComputable) {{
                        const percent = Math.round((e.loaded / e.total) * 100);
                        progressBar.style.width = percent + '%';
                        progressBar.innerText = percent + '%';
                        statusText.innerText = 'Enviando...';
                    }}
                }};

                xhr.onload = () => {{
                    if (xhr.status === 204 || xhr.status === 200) {{
                        // --- AQUI ESTÁ A CORREÇÃO PRINCIPAL ---
                        // Usamos a URL do CloudFront que a API mandou, não a do S3
                        const finalUrl = data.cloudfront_url; 
                        
                        urlInput.value = finalUrl; 
                        statusText.innerHTML = '<b style="color:green">✅ Sucesso! URL do CloudFront gerada.</b>';
                        
                        // Atualiza o preview na hora
                        const existingPreview = document.querySelector('.s3-direct-widget img');
                        if(existingPreview) {{
                            existingPreview.src = finalUrl;
                        }} else {{
                            // Se não tinha preview, cria um aviso visual
                            statusText.innerHTML += '<br><img src="' + finalUrl + '" style="max-height:100px; margin-top:5px; border:1px solid #ccc;">';
                        }}

                    }} else {{
                        statusText.innerText = '❌ Falha: ' + xhr.status;
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
        return mark_safe(output + html)
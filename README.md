# 🎥 Low-Cost Django Streaming

Uma aplicação de streaming de vídeos focada em custo mínimo, utilizando a arquitetura AWS Free Tier.

## 🏗 Arquitetura

O projeto foi desenhado para ser "Cloud Native" mas extremamente econômico:

* **Backend:** Django (Python) rodando em EC2 (t2.micro/t3.micro - Free Tier).
* **Banco de Dados:** SQLite (Armazenado no disco da EC2 para custo zero).
* **Storage (Vídeos):** AWS S3 (Armazenamento de objetos).
* **CDN (Opcional & Recomendado):** AWS CloudFront (Entrega rápida e HTTPS).
* **Servidor Web:** Nginx + Gunicorn.
* **CI/CD:** GitHub Actions (Deploy automático ao fazer push na `main`).

---

## 🚀 Como Rodar Localmente

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/seu-repo.git](https://github.com/seu-usuario/seu-repo.git)
    cd seu-repo
    ```

2.  **Crie o ambiente virtual:**
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate
    # Linux/Mac: source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure o `.env`:**
    Crie um arquivo `.env` na raiz (baseado no `.env.example`) e adicione suas credenciais AWS:
    ```ini
    DEBUG=True
    SECRET_KEY=sua-chave-secreta-local
    AWS_ACCESS_KEY_ID=xxx
    AWS_SECRET_ACCESS_KEY=xxx
    AWS_STORAGE_BUCKET_NAME=nome-do-bucket
    # Se usar CloudFront:
    AWS_S3_CUSTOM_DOMAIN=dxxxx.cloudfront.net
    ```

5.  **Rode as migrações e o servidor:**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

---

## ☁️ Configuração do Servidor (Produção)

Este setup precisa ser feito apenas **uma vez** na instância EC2.

### 1. Preparar o Sistema
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx git
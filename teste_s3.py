import boto3
import os

# Configuração
BUCKET_NAME = 'streaming-forro-pe-descalco'
REGION = 'us-east-1'

print(f"--- Testando acesso ao bucket: {BUCKET_NAME} ---")
try:
    # Tenta conectar sem chaves (usando IAM Role)
    s3 = boto3.client('s3', region_name=REGION)

    # Tenta listar objetos (valida leitura)
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)

    print("✅ SUCESSO! Conexão estabelecida via IAM Role.")
    if 'Contents' in response:
        print(f"Arquivos encontrados: {len(response['Contents'])}")
    else:
        print("Bucket acessado, mas está vazio.")

    # Tenta criar um arquivo (valida escrita)
    print("Tentando criar arquivo de teste...")
    s3.put_object(Bucket=BUCKET_NAME, Key='teste_iam.txt', Body='Funcionou!')
    print("✅ SUCESSO! Arquivo 'teste_iam.txt' criado.")

except Exception as e:
    print("\n❌ FALHA NO TESTE:")
    print(e)

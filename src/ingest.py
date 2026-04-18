import os
import pathlib
import sys
import kagglehub
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Validação de variáveis obrigatórias
# ---------------------------------------------------------------------------
_required_env = ["DATA_RAW_PATH"]
for _var in _required_env:
    if not os.getenv(_var):
        print(f"❌ Variável de ambiente obrigatória não definida: {_var}")
        sys.exit(1)

RAW_PATH = pathlib.Path(os.getenv("DATA_RAW_PATH", "data/raw"))
RAW_PATH.mkdir(parents=True, exist_ok=True)


def ingest() -> None:
    """Baixa o dataset Olist do Kaggle e converte cada CSV em Parquet (snappy)."""
    print("⏳ Baixando dataset olistbr/brazilian-ecommerce via kagglehub...")
    dataset_path = pathlib.Path(
        kagglehub.dataset_download("olistbr/brazilian-ecommerce")
    )
    print(f"✅ Dataset baixado em: {dataset_path}")

    csv_files = sorted(dataset_path.glob("*.csv"))
    if not csv_files:
        print(f"❌ Nenhum arquivo CSV encontrado em {dataset_path}")
        sys.exit(1)

    print(f"\n📦 Convertendo {len(csv_files)} arquivo(s) para Parquet...\n")
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, low_memory=False)
            out = RAW_PATH / csv_file.with_suffix(".parquet").name
            df.to_parquet(out, compression="snappy", index=False)
            print(f"✅ {out.name}: {len(df):,} linhas × {len(df.columns)} colunas")
        except Exception as exc:
            print(f"⚠️  Erro ao processar {csv_file.name}: {exc}")

    print("\n✅ Ingestão concluída.")


if __name__ == "__main__":
    ingest()

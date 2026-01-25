FROM public.ecr.aws/glue/aws-glue-libs:glue_libs_5_0_0

USER root

# Python依存パッケージをインストール
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt をコピーしてインストール
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

WORKDIR /workspace

# デフォルトのシェルを設定
CMD ["/bin/bash"]
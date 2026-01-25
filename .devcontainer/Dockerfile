# AWS Glue 5.0 のローカル開発環境
# 公式の AWS Glue Docker イメージを使用
# https://docs.aws.amazon.com/ja_jp/glue/latest/dg/develop-local-docker-image.html
FROM public.ecr.aws/glue/aws-glue-libs:5

USER root

# requirements.txt をコピーして Python パッケージをインストール
COPY requirements.txt .
RUN /usr/bin/python3.11 -m pip install --upgrade pip && \
    /usr/bin/python3.11 -m pip install --no-cache-dir -r requirements.txt

WORKDIR /workspace

# bash をシェルとして設定
ENV SHELL=/bin/bash
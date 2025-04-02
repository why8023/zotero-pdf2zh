FROM byaidu/pdf2zh:latest

WORKDIR /app

COPY main.py organize_pdf.py config.json /app/

RUN pip install --global -U pypdf

CMD ["python", "main.py", "--input", "/app/pdf/test.pdf", "--output", "/app/pdf", "--config", "/app/config.json", "--babeldoc", "--service", "google"]

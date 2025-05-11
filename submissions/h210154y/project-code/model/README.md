# Running Service 

Run the service:

- With GPU support:
  
      make start


- Without GPU support:

      make start_no_gpu


[OPTIONAL] OCR the PDF. Check supported languages (curl localhost:5060/info):

    curl -X POST -F 'language=en' -F 'file=@/PATH/TO/PDF/pdf_name.pdf' localhost:5060/ocr --output ocr_document.pdf


Get the segments from a PDF:

    curl -X POST -F 'file=@/PATH/TO/PDF/pdf_name.pdf' localhost:5060

To stop the server:

    make stop


## Dependencies
* Docker Desktop 4.25.0 [install link](https://www.docker.com/products/docker-desktop/)
* For GPU support [install link](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

## Requirements
* 2 GB RAM memory
* 4 GB GPU memory (if not, it will run on CPU)
  
## Summary 

The service converts PDFs to text-searchable PDFs using [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and [ocrmypdf](https://ocrmypdf.readthedocs.io/en/latest/index.html).
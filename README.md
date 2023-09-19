# Receipt-Scanner
Receipt scanners are used everywhere and they store the contents of the bill or receipts.

[dataset](https://www.kaggle.com/datasets/rahulsah06/data-extraction-from-receipt)


[info](https://drive.google.com/file/d/1JeyGfekkmkc5UxPU4V9T-Hb1UnkrA_cf/view)

`
curl --location 'http://0.0.0.0:52209/ai/extraction/receipt' \
--header 'Content-Type: application/json' \
--data '{
  "img_url": [
    "https://staging-persist.signzy.tech/api/files/4956704/download/cbb87bf7bd814302bd8ba1643b68f4d172323edf75c64fdb9bfb333a14a7e492.jpeg"
  ]
}'
`

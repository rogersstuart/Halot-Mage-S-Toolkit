import requests
from py_mini_racer import py_mini_racer


# URLs of the JavaScript libraries
pako_url = "https://cdnjs.cloudflare.com/ajax/libs/pako/2.1.0/pako.min.js"
crypto_js_url = "https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.js"

def download_js_library(url):
    response = requests.get(url)
    return response.text

def get_token(password):
    # Download the JavaScript libraries
    pako_code = download_js_library(pako_url)
    crypto_js_code = download_js_library(crypto_js_url)

    # JavaScript code as a string
    js_code = f"""
    

   function generateToken() {{
        var key = CryptoJS.enc.Hex.parse("6138356539643638");

        var password = "{password}";
        var encrypted = CryptoJS.DES.encrypt(password, key, {{
            mode: CryptoJS.mode.ECB,
            padding: CryptoJS.pad.Pkcs7
        }});

        var finalEncrypted = CryptoJS.enc.Base64.stringify(encrypted.ciphertext);

        // Return the encrypted value
        return finalEncrypted;
    }}

    generateToken();
    """



    js_code =  pako_code + crypto_js_code + js_code 

    # Execute the JavaScript code
    ctx = py_mini_racer.MiniRacer()
    result = ctx.eval(js_code)
    return result

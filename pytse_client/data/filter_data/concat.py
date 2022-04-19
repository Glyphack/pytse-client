from key_stats import filter_key_value
from bs4 import BeautifulSoup

with open("key_stats.html", "r") as f:
    mdfile = f.read()
    soup = BeautifulSoup(mdfile, features="lxml")
    tds = soup.find_all("td")
    titles = [td.text for td in tds[:2]]
    number, persian_explanation, symbol = None, None, None
    
    with open("key_stats.md", "w") as f2:
        f2.write("| شماره | توضیحات | سمبل |\n")
        f2.write("| --- | --- | --- |\n")
        
        for idx, td in enumerate(tds[2:]):
            if idx % 2 == 0:
                number = int(td.text)
            else:
                persian_explanation = td.text
                symbol = filter_key_value[number]    
                f2.write(f"| {number} | {persian_explanation} | {symbol} |\n")
                
        
        
        
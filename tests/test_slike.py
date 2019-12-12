import requests, io, os, sys, datetime
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance

pathname = os.path.dirname(sys.argv[0])
logginglog_directory = "/Log"
log_directory = pathname+logginglog_directory

req = requests.get('https://yugioh.fandom.com/wiki/30,000-Year_White_Turtle')
soup = BeautifulSoup(req.content, "html.parser")
try:
    card_image_link = soup.find("a", {"class": "image image-thumbnail"}).img[
        "src"]  # radi konzistentnosti, sve su 300pix
except AttributeError:
    card_image_link = soup.find("a", {"class": "image image-thumbnail"})["href"]
name = soup.find("td", {"class": "cardtablerowdata"}).text.strip()

image = requests.get(card_image_link, stream=True)
im = Image.open(io.BytesIO(image.content))
im = im.convert('RGB')
# print('Input file size       : ', im.size )
# print('Input file name       : ', name )
# print('Input Image Size      : ', sys.getsizeof(image.content))
# print('')

enhancer = ImageEnhance.Sharpness(im)
factor = 1.8
en_im = enhancer.enhance(factor)

im_save_name = os.path.normpath(f'''{pathname}/Images/Spell/Continuous/{name.replace('"', '').replace(' ', '_')}.jpg''')
en_im.save(im_save_name)
# Image path for DB
card_image = im_save_name
print(card_image)

# print('Output file size       : ', en_im.size )
# print('Output file name       : ', im_save_name)
# print('Sharepned Image Size   : ', os.path.getsize (im_save_name))
# print('Sharpness level set to : ', factor)
# print('---------------------------------------------------\n')
try:
    with open(f"{log_directory}/card_image_size_log.txt", "a") as log:
        log.write(
            "{}\n{}  |  Sharpening of card : {}\n".format(0,
                                                          datetime.datetime.now().strftime(
                                                              "%d/%m/%Y, %H:%M:%S"),
                                                          "Spell"))
        log.write("Original size : {}\n".format(sys.getsizeof((image.content))))
        log.write("New size      : {}\n".format(os.path.getsize((card_image))))
        log.write("---------------------------------------------------------\n")
        log.flush()

# urllib.request.urlretrieve(card_image_link, "{}.jpg.".format(name.replace(" ", "_")) # manje function calls prema profiler-u
# with open("{}.jpg.".format(name.replace(" ", "_")),"wb") as pic:
#   pic.write(card_image.content)
except Exception as e:
    print("Nema slike : ", e)
    with open(f"{log_directory}/card_image_log.txt", "a") as log:
        log.write(
            "{}\n{}  |  Missing card image : {}\n".format(0,
                                                          datetime.datetime.now().strftime(
                                                              "%d/%m/%Y, %H:%M:%S"),
                                                          "spell"))
        log.write("---------------------------------------------------------\n")
        log.flush()
card_image = ""  # file path

print("Process ended : ", 0)
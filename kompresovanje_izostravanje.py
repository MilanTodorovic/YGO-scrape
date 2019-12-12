from PIL import Image, ImageEnhance
import os, requests, io, sys

print('*** Program Started ***')

#image = requests.get("https://vignette.wikia.nocookie.net/yugioh/images/a/ad/DarkMagicianofChaos-DUSA-EN-UR-1E.png/revision/latest?cb=20170330171821", stream=True)

image_name_input = 'b-300.png'
im = Image.open(image_name_input)
im = im.convert('RGB')
#im = Image.open(io.BytesIO(image.content))

print('Input file size       : ', im.size )
print('Input file name       : ', "Areil" )
print('Input Image Size      : ', os.path.getsize(image_name_input)) #sys.getsizeof((image.content))
print('')

enhancer = ImageEnhance.Sharpness(im)

factor = 2.0
en_im = enhancer.enhance(factor)
en_im.save(image_name_input+"_sh.jpg")
print('Output file size       : ', en_im.size )
print('Output file name       : ', image_name_input+"_sh.jpg")
print('Sharepned Image Size   : ', os.path.getsize (image_name_input+"_sh.jpg"))
print('Sharpness level set to : ', factor)
print('---------------------------------------------------\n')
'''
quality = [100, 90, 80, 70, 60, 50]
for q in quality:
    image_name_output = 'dm_compressed_{}.jpg'.format(str(q))
    image_name_output_sharpened = 'dm_compressed_sharpened_{}.jpg'.format(str(q))
    im.save(image_name_output ,optimize=True,quality=q)

    print('Output file size       : ', im.size )
    print('Output file name       : ', image_name_output)
    print('Output Image Size      : ', os.path.getsize (image_name_output))
    print('Quality set to         : ', q)
    print('')

    enhancer = ImageEnhance.Sharpness(im)

    factor = 2.0
    en_im = enhancer.enhance(factor)
    en_im.save(image_name_output_sharpened)
    print('Output file size       : ', en_im.size )
    print('Output file name       : ', image_name_output_sharpened)
    print('Sharepned Image Size   : ', os.path.getsize (image_name_output_sharpened))
    print('Sharpness level set to : ', factor)
    print('---------------------------------------------------\n')
'''
print('*** Program Ended ***')
    

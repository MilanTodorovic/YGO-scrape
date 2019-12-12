import os, multiprocessing

def make_file(number):
    os.makedirs("/asd")
    #for i in range(number, number+10):
    #    with open(os.path.normpath(f"slike_dm/fajl{i}.txt"), "w") as file:
    #        file.write("asdasd") # mora svugde \n
    #        file.write("++++asdasdas")
    #        file.writelines("asdasdasd")

if __name__ == "__main__":
    for i in range(2):
        p = multiprocessing.Process(target=make_file, args=(10*i,))
        p.start()

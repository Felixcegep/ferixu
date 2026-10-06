#Feu tricolore ARD-625

from pydantic import BaseModel, ConfigDict, Field

from gpiozero import LED


class FeuCirculation:
    del_rouge = LED(27)
    del_jaune = LED(22)
    del_verte = LED(23)


    def allumerRouge(self):
        self.del_jaune.off()
        self.del_verte.off()
        self.del_rouge.on()

    def allumerJaune(self):
        self.del_jaune.on()
        self.del_verte.off()
        self.del_rouge.off()

    def allumerVert(self):
        self.del_jaune.off()
        self.del_verte.on()
        self.del_rouge.off()

    def eteindre(self):
        self.del_jaune.off()
        self.del_verte.off()
        self.del_rouge.off()


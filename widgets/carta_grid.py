from kivy.uix.recycleview import RecycleView


class CartaGrid(RecycleView):
    cartas = [{"valor": v, "palo": p} for v in ["As","2","3","4","5","6","7","Sota","Reina","Rey"]
                                for p in ["Oros","Copas","Espadas","Bastos"]]

    def mostrar_filtro(self, valor, palo):
        print("Filtrando")
        print("VALOR ", valor)
        print("PALO ", palo)
        if valor == "Selecciona un valor":
            valor = ""
        if palo == "Selecciona un palo":
            palo = ""

        if valor and palo:
            print("BOTH")
            self.data = [{"text": f"{c['valor']} de {c['palo']}"} 
                         for c in self.cartas if c["valor"] == valor and c["palo"] == palo]
        elif valor:
            print("VALUE")
            self.data = [{"text": f"{c['valor']} de {c['palo']}"} 
                         for c in self.cartas if c["valor"] == valor]
        elif palo:
            print("PLAO")
            self.data = [{"text": f"{c['valor']} de {c['palo']}"} 
                         for c in self.cartas if c["palo"] == palo]
        else:
            print("NADa")
            self.data = [{"text": f"{c['valor']} de {c['palo']}"} for c in self.cartas]

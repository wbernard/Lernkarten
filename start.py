#!/usr/bin/python3
import gi
import sys
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import sqlite3

from gi.repository import Gtk, Adw, Gio, GLib, Gdk, GObject

'''
Klassen:
- KarteiWahlUndNeu
- KartenListe
- KarteNeu
- Karte
- Spiel
'''       

class KarteiWahlUndNeu(Gtk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Karteien")
        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(titlebar=self.headerbar)
        self.application = kwargs.get('application')
        
        self.set_default_size(400, 400)
        self.set_size_request(400, 400)

        db_name = 'karteibox.db'
        os.getcwd() #return the current working directory
           
        for root, dirs, files in os.walk(os.getcwd()):
            if db_name in files:  # wenn es eine Datenbank für die Karteibox gibt wird sie aufgerufen                         
                self.hole_karteien()
                break
            else:
                self.kartei_liste = Gtk.ListStore(int, str)
            
        
        # App menu  - Menu in der Kopfleiste   
        self.menu_button_model = Gio.Menu()
        self.menu_button_model.append("about_app", 'app.about')
        self.menu_button = Gtk.MenuButton.new()
        self.menu_button.set_icon_name(icon_name='open-menu-symbolic')
        self.menu_button.set_menu_model(menu_model=self.menu_button_model)
        self.headerbar.pack_end(child=self.menu_button)

        # das ist das dropdown-menu links in der Kopfleiste
        self.savedesktop_mode_dropdwn = Gtk.DropDown.new_from_strings( \
            "save_config" )
        #self.savedesktop_mode_dropdwn.connect('notify::selected-item', \
            #self.change_savedesktop_mode)
        
        # Primary layout
        self.pBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.pBox.set_halign(Gtk.Align.CENTER)
        #self.pBox.set_valign(Gtk.Align.CENTER)
        self.pBox.set_margin_start(50)
        self.pBox.set_margin_end(50)


        self.sw = Gtk.ScrolledWindow()  # Fenster mit Rollbalken
        #self.sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.sw.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.ALWAYS) # horizontal kein Balken, vertikal immer
        self.sw.set_size_request(150,180)
        self.sw.set_margin_top(10)
        self.pBox.append(self.sw)
        
        self.list_ansicht = Gtk.TreeView() # hier stehen die vorhandenen Karteien
        self.list_ansicht.set_model(self.kartei_liste)
        self.sw.set_child(self.list_ansicht)

        spal_titel = ["oid", "Doppelklick öffnet Kartei"] 
        for i in range(1,2):
            rendererText = Gtk.CellRendererText(xalign=0.0, editable=False)
            column = Gtk.TreeViewColumn(spal_titel[i], rendererText, text=i)
            column.set_cell_data_func(rendererText, self.celldata, func_data=i)
            self.list_ansicht.append_column(column)
   
        self.list_ansicht.set_property('activate-on-single-click', False) # Reihe wird mit einem Klick aktiv
        self.list_ansicht.connect('row-activated', self.auswahl)
        
        self.eing1 = Gtk.Entry()    # Eingabefenster
        self.eing1.set_width_chars(20)
        self.eing1.add_css_class("card")
        self.eing1.set_margin_top(10)
        self.eing1.set_placeholder_text("Name der neuen Kartei")
        self.pBox.append(self.eing1)        
      
        # Toast
        self.toast_overlay = Adw.ToastOverlay.new()
        self.toast_overlay.set_margin_top(margin=1)
        self.toast_overlay.set_margin_end(margin=1)
        self.toast_overlay.set_margin_bottom(margin=1)
        self.toast_overlay.set_margin_start(margin=1)
        
        self.set_child(self.toast_overlay)
        self.toast_overlay.set_child(self.pBox)
        
        self.toast = Adw.Toast.new(title='')
        self.toast.set_timeout(5)
        self.toast.connect('dismissed', self.on_toast_dismissed)
        
        self.create_window()
        self.headerbar.pack_start(self.savedesktop_mode_dropdwn)
        
    def celldata(self, col, cell, mdl, itr, i):   # Formattiert die Ausgabe der Datenansicht
    # col = Columnn, cell = Cell, mdl = model, itr = iter, i = column number
    # column is provided by the function, but not used
        value = mdl.get(itr,i)[0]
        if type(value) is not str:
            cell.set_property('text',f'{value+0.005:.2f}')  # Anzahl der Kommastellen
        path = mdl.get_path(itr)
        row = path[0]
        colors = ['white', 'lightgrey']
    # set alternating backgrounds
        cell.set_property('cell-background', colors[row % 2])

    def hole_karteien(self):
        conn = sqlite3.connect('karteibox.db')
       # eine cursor instanz erstellen
        c = conn.cursor()

        #self.kartei_liste = Gtk.ListStore(int, str)  # Liste der vorhandenen Karteien
        c.execute("select rowid, kartei from karteibox")   # die originale id und der Karteiname wird geholt
        liste = c.fetchall()
            #self.kartei_liste.append(row)
        print ('Liste', liste)
        self.kartei_liste = Gtk.ListStore(int, str)  # Liste der vorhandenen Karteien
        self.alle_karteien = []
        for zeile in liste:
            #print('Kartei', zeile) 
            if not list(zeile)[1] in self.alle_karteien: # nur neue Karteien kommen auf die Liste
                self.alle_karteien.append(list(zeile)[1])
        n = 0
        for kartei in self.alle_karteien: # in der ListStore ist jede Kartei nur einmal
            weitere_kartei = [n,kartei]
            self.kartei_liste.append(weitere_kartei)
            n += 1
                
        print('alle_karteien',self.alle_karteien)
        #print('LIST-KARTEI',list(kartei)[1])

        conn.commit()
        conn.close()   # Verbindung schließen
    
    # Show main layout
    def create_window(self):
        
        # Box für das Erstellen der Kartei
        self.saveBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.pBox.append(self.saveBox)
        
        self.btnBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.btnBox.set_margin_top(10)
        self.btnBox.set_margin_start(40)
        self.btnBox.set_margin_end(40)
        self.saveBox.append(self.btnBox)
        
        self.saveButton = Gtk.Button.new_with_label("Speichere neue Kartei")
        self.saveButton.add_css_class("suggested-action")
        self.saveButton.add_css_class("pill")
        self.saveButton.connect("clicked", self.neue_kartei)
        self.btnBox.append(self.saveButton)

    def auswahl(self, list_ansicht, zeile, column): # ein Event wird übergeben wg Einbindung Baumansicht
        # ausgewählte Zeile übergibt die Daten
        # Auswahl der angeklickten Zeile
        selection = self.list_ansicht.get_selection()
        selected = selection.get_selected()
        model = self.list_ansicht.get_model() # ListStore der Ansicht
        #print(zeile)
        zeiger = model.get_iter(zeile)  # Adresse zur gewählten Zeile
        #print(zeiger, len(model))
        werte = []
        for i in range(2):
            wert = model.get_value(zeiger, i)
            werte.append(wert)  # die ersten beiden Werte werden gespeichert

        self.oid = werte[0]   # die ID der Zeile wird gespeichert
        # Ausgabe in die Eingabefelder
        self.name = werte[1]
        self.eing1.set_placeholder_text(self.name)

        self.oeffne_kartei()


    def oeffne_kartei(self):
        win1 = KarteiWahlUndNeu()
        win1.hide()  # schließt das Fenster der Karteikartenbox

        win2 = KartenListe(self.name)
        win2.present()   
        pass

    def neue_kartei(self, w):                
        name = self.eing1.get_text()
        os.getcwd() #return the current working directory
        print (name)  
        for root, dirs, files in os.walk(os.getcwd()):
            if 'karteibox.db' in files:  # wenn es eine Datenbank für die Karteibox gibt wird sie aufgerufen                         
                conn = sqlite3.connect('karteibox.db')        
                c = conn.cursor() # eine cursor instanz erstellen
                c.execute("""INSERT INTO karteibox VALUES (
                            :kartei, :karte_vorn, :karte_hinten)""",              
                            {'kartei': name, 'karte_vorn': ' ',
                             'karte_hinten': ' '})
                print(name)
                conn.commit()    # Änderungen mitteilen
                for row in c.execute("select * from karteibox"):
                    print (row)
                break
            else:
                conn = sqlite3.connect('karteibox.db')        
                c = conn.cursor() # eine cursor instanz erstellen
                # Tabelle mit Karteien
                c.execute("""CREATE TABLE if not exists karteibox (
                                  kartei TEXT, karte_vorn TEXT, karte_hinten TEXT)""")
                c.execute("""INSERT INTO karteibox VALUES (
                            :kartei, :karte_vorn, :karte_hinten)""",              
                            {'kartei': name, 'karte_vorn': ' ',
                             'karte_hinten': ' '})
                print(name)
                conn.commit()    # Änderungen mitteilen
                for row in c.execute("select * from karteibox"):
                    print (row)
                conn.close()   # Verbindung schließen

        win1 = KarteiWahlUndNeu()
        win1.hide()  # schließt das Fenster der Karteikartenbox

        win1 = KarteiWahlUndNeu()
        win1.present()   
        pass
  
                
    def on_toast_dismissed(self, toast):
        os.popen("rm -rf %s/*" % CACHE)
        os.popen("rm -rf {}/SaveDesktop/.{}/*".format(download_dir, date.today()))
       
class KartenListe(Gtk.Window):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title(name)
        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(titlebar=self.headerbar)
        self.application = kwargs.get('application')
        self.name = name
        
        self.set_default_size(400, 400)
        self.set_size_request(400, 400)
        
        self.hole_karten()

        # das ist das dropdown-menu links in der Kopfleiste
        self.savedesktop_mode_dropdwn = Gtk.DropDown.new_from_strings( \
            "save_config" )
        self.savedesktop_mode_dropdwn.connect('notify::selected-item', \
            self.change_savedesktop_mode)
        
        # Primary layout
        self.pBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.pBox.set_halign(Gtk.Align.CENTER)
        #self.pBox.set_valign(Gtk.Align.CENTER)
        self.pBox.set_margin_start(50)
        self.pBox.set_margin_end(50)

        self.sw = Gtk.ScrolledWindow()  # Fenster mit Rollbalken
        #self.sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.sw.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.ALWAYS) # horizontal kein Balken, vertikal immer
        self.sw.set_size_request(150,200)
        self.pBox.append(self.sw)
                
        self.list_ansicht = Gtk.TreeView()
        self.list_ansicht.set_model(self.karten_liste)  
        self.sw.set_child(self.list_ansicht)

        spal_titel = ["oid", "Doppelklick öffnet Karteikarte"] 
        for i in range(1,2):
            rendererText = Gtk.CellRendererText(xalign=0.0, editable=False)
            column = Gtk.TreeViewColumn(spal_titel[i], rendererText, text=i)
            column.set_cell_data_func(rendererText, self.celldata, func_data=i)
            self.list_ansicht.append_column(column)
            
        self.list_ansicht.set_property('activate-on-single-click', False) # Reihe wird mit einem Klick aktiv
        self.list_ansicht.connect('row-activated', self.auswahl)
        '''
        self.eing1 = Gtk.Entry()    # Eingabefenster
        self.eing1.set_width_chars(20)
        self.eing1.add_css_class("card")
        self.eing1.set_margin_top(10)
        self.eing1.set_placeholder_text("Name der neuen Karteikarte")
        self.pBox.append(self.eing1)   '''     
      
        # Toast
        self.toast_overlay = Adw.ToastOverlay.new()
        self.toast_overlay.set_margin_top(margin=1)
        self.toast_overlay.set_margin_end(margin=1)
        self.toast_overlay.set_margin_bottom(margin=1)
        self.toast_overlay.set_margin_start(margin=1)
        
        self.set_child(self.toast_overlay)
        self.toast_overlay.set_child(self.pBox)
        
        self.toast = Adw.Toast.new(title='')
        self.toast.set_timeout(5)
        self.toast.connect('dismissed', self.on_toast_dismissed)
        
        self.create_window()
        self.headerbar.pack_start(self.savedesktop_mode_dropdwn)
        
    def celldata(self, col, cell, mdl, itr, i):   # Formattiert die Ausgabe der Datenansicht
    # col = Columnn, cell = Cell, mdl = model, itr = iter, i = column number
    # column is provided by the function, but not used
        value = mdl.get(itr,i)[0]
        if type(value) is not str:
            cell.set_property('text',f'{value+0.005:.2f}')  # Anzahl der Kommastellen
        path = mdl.get_path(itr)
        row = path[0]
        colors = ['white', 'lightgrey']
    # set alternating backgrounds
        cell.set_property('cell-background', colors[row % 2])

    def hole_karten(self):
        conn = sqlite3.connect('karteibox.db')
       # eine cursor instanz erstellen
        c = conn.cursor()

        c.execute("select * from karteibox where kartei=:c", {"c": self.name})   # die originale id und der Karteiname wird geholt
        liste = c.fetchall()
            #self.kartei_liste.append(row)
        print ('liste', liste) # alle Karten der Kartei
        self.alle_karten = []
        for zeile in liste:
            if list(zeile)[1] != ' ':  # ergibt Liste aller Karten mit Namen
                self.alle_karten.append(list(zeile)[1])
                
        print('alle_karten',self.alle_karten)

        self.karten_liste = Gtk.ListStore(int, str)  # Liste der vorhandenen Karteien
        n = 0
        for karte in self.alle_karten: # in der ListStore ist jede Kartei nur einmal
            weitere_karte = [n,karte]
            self.karten_liste.append(weitere_karte)
            n += 1

        conn.commit()
        conn.close()   # Verbindung schließen
    
    def change_savedesktop_mode(self, w, pspec):
        if self.savedesktop_mode_dropdwn.get_selected() == 0:
            self.create_window()
        else:
            self.import_desktop()
    
    # Show main layout
    def create_window(self):
        
        # Box für das Erstellen der Kartei
        self.saveBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.pBox.append(self.saveBox)
                       
        self.btnBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.btnBox.set_margin_top(10)
        self.btnBox.set_margin_start(40)
        self.btnBox.set_margin_end(40)
        self.saveBox.append(self.btnBox)
        
        self.saveButton = Gtk.Button.new_with_label("Neue Karte")
        self.saveButton.add_css_class("suggested-action")
        self.saveButton.add_css_class("pill")
        self.saveButton.connect("clicked", self.neue_karte)
        self.btnBox.append(self.saveButton)
        
    def auswahl(self, list_ansicht, zeile, column): # ein Event wird übergeben wg Einbindung Baumansicht
        # ausgewählte Zeile übergibt die Daten
        # Auswahl der angeklickten Zeile
        selection = self.list_ansicht.get_selection()
        selected = selection.get_selected()
        model = self.list_ansicht.get_model() # ListStore der Ansicht
        #print(zeile)
        zeiger = model.get_iter(zeile)  # Adresse zur gewählten Zeile
        #print(zeiger, len(model))
        werte = []
        for i in range(2):  # in der karten_liste sind nur 2 Spalten oid und name
            wert = model.get_value(zeiger, i)
            werte.append(wert)  # die ersten beiden Werte werden gespeichert

        self.oid = werte[0]   # die ID der Zeile wird gespeichert
        # Ausgabe in die Eingabefelder
        self.kart = werte[1]
        
        #self.eing1.set_placeholder_text(self.kart)

        self.zeige_karte()

    def zeige_karte(self):
        win2 = KartenListe(self.name)
        win2.hide()  # schließt das Fenster der Karteikartenbox
        
        win3 = Karte(self.name, self.kart)
        win3.present()   
        pass

    def neue_karte(self, w):
        #self.kart = self.eing1.get_text()
        win2 = KartenListe(self.name)
        win2.hide()  # schließt das Fenster der Karteikartenbox
        win3 = KarteNeu(self.name)        
        #win3 = KarteNeu(self.name, self.kart)
        win3.present()   
        
    def on_toast_dismissed(self, toast):
        os.popen("rm -rf %s/*" % CACHE)
        os.popen("rm -rf {}/SaveDesktop/.{}/*".format(download_dir, date.today()))
       
class KarteNeu(Gtk.Window):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title('Neue Karte')
        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(titlebar=self.headerbar)
        self.application = kwargs.get('application')
        self.name =name
        #self.kart = kart
        
        self.set_default_size(300, 300)
        self.set_size_request(00, 300)
        
        # Primary layout
        self.pBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.pBox.set_halign(Gtk.Align.CENTER)
        #self.pBox.set_valign(Gtk.Align.CENTER)
        self.pBox.set_margin_start(20)
        self.pBox.set_margin_end(20)
  
        self.eing1 = Gtk.Entry()    # Eingabefenster
        self.eing1.set_width_chars(20)
        self.eing1.add_css_class("card")
        self.eing1.set_margin_top(10)
        self.eing1.set_placeholder_text('Vorderseite der Karte')        
        #self.eing1.set_text(self.kart)
        self.pBox.append(self.eing1)        
      
        self.eing2 = Gtk.Entry()    # Eingabefenster
        self.eing2.set_width_chars(20)
        self.eing2.add_css_class("card")
        self.eing2.set_margin_top(10)
        self.eing2.set_placeholder_text('Rückseite der Karte')
        self.pBox.append(self.eing2)        

        # Toast
        self.toast_overlay = Adw.ToastOverlay.new()
        self.toast_overlay.set_margin_top(margin=1)
        self.toast_overlay.set_margin_end(margin=1)
        self.toast_overlay.set_margin_bottom(margin=1)
        self.toast_overlay.set_margin_start(margin=1)
        
        self.set_child(self.toast_overlay)
        self.toast_overlay.set_child(self.pBox)
        
        self.toast = Adw.Toast.new(title='')
        self.toast.set_timeout(5)
        self.toast.connect('dismissed', self.on_toast_dismissed)
        
        self.create_window()

    # Show main layout
    def create_window(self):
        
        # Box für das Erstellen der Kartei
        self.saveBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.pBox.append(self.saveBox)
                       
        self.btnBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.btnBox.set_margin_top(10)
        self.btnBox.set_margin_start(40)
        self.btnBox.set_margin_end(40)
        self.saveBox.append(self.btnBox)
        
        self.saveButton = Gtk.Button.new_with_label("Speichere neue Karte")
        self.saveButton.add_css_class("suggested-action")
        self.saveButton.add_css_class("pill")
        self.saveButton.connect("clicked", self.speichere_karte)
        self.btnBox.append(self.saveButton)

    def speichere_karte(self, w):
        name = self.name
        kart = self.eing1.get_text()
        kart_hint = self.eing2.get_text()
        os.getcwd() #return the current working directory
        conn = sqlite3.connect('karteibox.db')        
        c = conn.cursor() # eine cursor instanz erstellen
            # Tabelle mit Karteien
        c.execute("""INSERT INTO karteibox VALUES (
                    :kartei, :karte_vorn, :karte_hinten)""",              
                    {'kartei': name, 'karte_vorn': kart ,
                    'karte_hinten': kart_hint})
        print(name)
        conn.commit()    # Änderungen mitteilen
        for row in c.execute("select * from karteibox"):
            print (row)
        conn.close()   # Verbindung schließen

        win3 = KarteNeu(self.name)
        win3.hide()   
        win2 = KartenListe(self.name)
        win2.present()  # schließt das Fenster der Karteikartenbox

      
    def on_toast_dismissed(self, toast):
        os.popen("rm -rf %s/*" % CACHE)
        os.popen("rm -rf {}/SaveDesktop/.{}/*".format(download_dir, date.today()))

class Karte(Gtk.Window):
    def __init__(self, name, kart, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title(name)
        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(titlebar=self.headerbar)
        self.application = kwargs.get('application')
        self.name =name
        self.kart = kart
        
        self.set_default_size(300, 300)
        self.set_size_request(300, 300)

        self.kart_daten()
        
        # Primary layout
        self.pBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.pBox.set_halign(Gtk.Align.CENTER)
        #self.pBox.set_valign(Gtk.Align.CENTER)
        self.pBox.set_margin_start(20)
        self.pBox.set_margin_end(20)
  
        self.eing1 = Gtk.Label()    # Eingabefenster
        self.eing1.set_width_chars(20)
        self.eing1.add_css_class("card")
        self.eing1.set_margin_top(10)
        self.eing1.set_text(self.kart)
        self.pBox.append(self.eing1)        
      
        self.eing2 = Gtk.Entry()    # Eingabefenster
        self.eing2.set_width_chars(20)
        self.eing2.add_css_class("card")
        self.eing2.set_margin_top(10)
        self.eing2.set_text(self.kart_hint)
        self.pBox.append(self.eing2)        

        # Toast
        self.toast_overlay = Adw.ToastOverlay.new()
        self.toast_overlay.set_margin_top(margin=1)
        self.toast_overlay.set_margin_end(margin=1)
        self.toast_overlay.set_margin_bottom(margin=1)
        self.toast_overlay.set_margin_start(margin=1)
        
        self.set_child(self.toast_overlay)
        self.toast_overlay.set_child(self.pBox)
        
        self.toast = Adw.Toast.new(title='')
        self.toast.set_timeout(5)
        self.toast.connect('dismissed', self.on_toast_dismissed)
        
        self.create_window()

    # Show main layout
    def create_window(self):
        
        # Box für das Erstellen der Kartei
        self.saveBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.pBox.append(self.saveBox)
                       
        self.btnBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.btnBox.set_margin_top(10)
        self.btnBox.set_margin_start(40)
        self.btnBox.set_margin_end(40)
        self.saveBox.append(self.btnBox)
        
        self.saveButton = Gtk.Button.new_with_label("Ändere Rückseite")
        self.saveButton.add_css_class("suggested-action")
        self.saveButton.add_css_class("pill")
        self.saveButton.connect("clicked", self.speichere_karte)
        self.btnBox.append(self.saveButton)

        self.Taste = Gtk.Button.new_with_label("Zurück zur Kartenliste")
        self.Taste.add_css_class("suggested-action")
        self.Taste.add_css_class("pill")
        self.Taste.connect("clicked", self.zu_kartliste)
        self.btnBox.append(self.Taste)

    def kart_daten(self):
        name = self.name
        kart = self.kart

        conn = sqlite3.connect('karteibox.db')        
        c = conn.cursor() # eine cursor instanz erstellen
            # Tabelle mit Karteien
        c.execute("select * from karteibox where kartei=:c and karte_vorn=:d", {"c": self.name, "d":self.kart})   # die originale id und der Karteiname wird geholt
        zeile = c.fetchall()
        self.kart_hint = zeile[0][2]
        
        conn.commit()    # Änderungen mitteilen
        conn.close()   # Verbindung schließen

    def speichere_karte(self, w):
        name = self.name
        kart = self.eing1.get_text()
        kart_hint = self.eing2.get_text()
        os.getcwd() #return the current working directory
        conn = sqlite3.connect('karteibox.db')        
        c = conn.cursor() # eine cursor instanz erstellen
            # Tabelle mit Karteien
        c.execute("""INSERT INTO karteibox VALUES (
                    :kartei, :karte_vorn, :karte_hinten)""",              
                    {'kartei': name, 'karte_vorn': kart ,
                    'karte_hinten': kart_hint})
        print(name)
        conn.commit()    # Änderungen mitteilen
        for row in c.execute("select * from karteibox"):
            print (row)
        conn.close()   # Verbindung schließen
        
        zu_kartliste()

    def zu_kartliste(self,w):
        win4 = Karte(self.name, self.kart)
        win4.hide()   
        win2 = KartenListe(self.name)
        win2.present()  
        
      
    def on_toast_dismissed(self, toast):
        os.popen("rm -rf %s/*" % CACHE)
        os.popen("rm -rf {}/SaveDesktop/.{}/*".format(download_dir, date.today()))
  
class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect('activate', self.on_activate)
    
    def on_activate(self, app):
        '''db_name = 'karteibox.db'
        os.getcwd() #return the current working directory
           
        for root, dirs, files in os.walk(os.getcwd()):
            if db_name in files:  # wenn es eine Datenbank für die Karteibox gibt wird sie aufgerufen                         
                self.win = KarteiWahl(application=app)
                self.win.present()
                break
            else:
                self.win = KarteiNeu(application=app)
                self.win.present()
                break '''
        
        self.win = KarteiWahlUndNeu(application=app)
        self.win.present()
        
        
app = MyApp()
app.run(sys.argv)

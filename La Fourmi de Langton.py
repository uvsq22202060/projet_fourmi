import ctypes, os, platform, json, tkinter as tk, time as t
from tkinter import ttk, filedialog, colorchooser

print("\033c")

# =============== Initiation TK =============

racine = tk.Tk()

if platform.system() == "Windows" or platform.system() == "Linux": ctypes.windll.shcore.SetProcessDpiAwareness(1)# contourne la mise à l'échelle de l'affichage de windows et linux
else: racine.tk.call('tk', 'scaling', 0.5) # solution temp pour mac

# ========== Chargement des Icones ==========

icon_names = ["Logo", "Pause", "Play", "Backwards", "Forwards", "Speed 1", "Speed 2", "Speed 3", "Add Ant", "Zoom In", "Zoom Out", "Load", "Save", "Escape", "Stop", "Cross"] # Nom des Icones
program_icons = dict(zip(icon_names, [None] * len(icon_names))) # dictionaire avec {Nom Icone : tk.photoImage(icone)}  

program_folder_path = os.path.dirname(__file__) # inspiration : https://stackoverflow.com/questions/61485360/opening-a-file-from-other-directory-in-python
for icon in program_icons: #insère le tk.PhotoImage dans la clé/nom correspondant dans program_icons
    program_icons[icon] = tk.PhotoImage(file = os.path.join(program_folder_path, "Icons", icon + ".png"))

# ================== Var ====================

Running        = False
create_window  = None # Tk() de la fenetre creation fourmi

refesh_counter = 0 # étapes jusqu'à l'actualisation du canvas
total_steps    = 0 # nombres de steps que la fourmie fait depuis l'etat initial
Height, Width  = 650, 650 # Dimensions du canvas
taille_grille  = [10, 20, 30, 50, 70, 100, 150, 200, 500] # Tailles Du Terrain
nombre_case    = taille_grille[3] + 1 # Nombre de cases dans le jeu | Doit etre impaire si on veut un milieu
field          = [["white" for _ in range(nombre_case)] for cell in range(nombre_case)] # liste 2D 50x50 remplie de "w"
grid_l_types   = ["", "black"] # symbole des types de la grille du canvas
Grid_Line      = grid_l_types[1] # symbole de deafaut de la grille du canvas

vitesses       = [(0.5, program_icons["Speed 1"]), (0.1, program_icons["Speed 2"]), (0, program_icons["Speed 3"])] # Les differantes vitesses du jeu | num = temps de sleep, txt = text du boutton
vitesse_jeu    = vitesses[0] # Vitesse du jeu par defaut
directions     = ["0", "90", "180", "-90"] # Directions de la fourmi

fourmi_objs    = [{"sym" : 0, "pos" : [nombre_case // 2,nombre_case // 2], "start_pos" : [nombre_case // 2,nombre_case // 2], "direction" : directions[0], "start_direction" : directions[0], "case_actuelle" : "white", "couleur" : "red", "obj" : "None"}] # l'object/dictionaire fourmi = symbole | position | direction | case actuelle | couleur | canvas.rectangle int

symbol         = fourmi_objs[-1]["sym"] + 1 if fourmi_objs else 0 # symbol de la fourmi par defaut
pos            = [nombre_case // 2,nombre_case // 2] # position de la fourmi par defaut
direction      = directions[0] # direction de la fourmi par defaut
fourmi_color   = "red"  # couleur de la fourmi par defaut

# ========== Func ==========

def tk_key_control(event):
    '''Takes control of Keyboard Input'''
    if event.char == "g":
        toggle_grid_lines()


def quitter(*args):
    '''Ferme le programme'''
    global Running, create_window
    
    if Running: Running = False
    if create_window:
        create_window.destroy()
    racine.destroy()


def pause():
    '''Met en pause le jeu'''
    global Running
    bouton_Start.config(image = program_icons["Play"])
    Running = False


def charger(*args):
    '''Ouvre une fenetre pour charger un fichier txt qui a une sauvegarede d'un jeu'''
    global fourmi_objs, field, total_steps, nombre_case, Running

    if Running: pause()
    fichier = filedialog.askopenfilename(title = "Charger une partie", filetypes = (('Text Document', '*.txt'),("Tous les fichiers", "*.*")))
    if fichier:
        with open(fichier, "r") as f:
            save_file   = f.read().replace("'", '"')
            fourmi_objs = json.loads(save_file[save_file.index("fourmis\n\n") + len("fourmis\n\n") : save_file.index("\n\n// Etat")])
            field       = json.loads(save_file[save_file.index("Terrain\n\n") + len("Terrain\n\n") : save_file.index("\n\n// Variables")])
            total_steps , nombre_case = json.loads(save_file[save_file.index("Variables\n\n") + len("Variables\n\n") : save_file.index("\n\nEnd")])
    label_steps.config(text = f"Step: {total_steps}")
    cbox_field_taille.set(f"Taille Terrain: {nombre_case - 1}x{nombre_case - 1}")
    canvas_refresh(); Canvas.update()


def sauvegarder(*args): 
    '''Ouvre une fenetre pour savegarder la parie en cours'''
    global Running

    if Running: pause()
    fichier = filedialog.asksaveasfile(filetypes = [('Text Document', '*.txt')], defaultextension = [('Text Document', '*.txt')])
    if fichier:
        with open(fichier.name, "w") as f:
            f.write(f"// Object fourmis\n\n{fourmi_objs}\n\n")
            f.write(f"// Etat du Terrain\n\n{field}\n\n")
            f.write(f"// Variables\n\n{[total_steps, nombre_case]}\n\nEnd")


def avancer(*args):
    '''Fait avencer le jeu d'une unité de temps'''
    if Running: pass
    else: fourmi_update()


def start(*args):
    '''Fait tourner le jeu'''
    global Running
    
    if Running: pause()
    else:
        Running = True
        bouton_Start.config(image = program_icons["Pause"])
        while Running:
            fourmi_update()
            t.sleep(vitesse_jeu[0])


def changer_vitesse(*args):
    '''Change la vitesse du jeu'''
    global vitesses, vitesse_jeu

    if not args or args[0].keysym == "Up":
        vitesse_jeu = vitesses[0] if vitesse_jeu == vitesses[-1] else vitesses[vitesses.index(vitesse_jeu) + 1]  
    elif args[0].keysym == "Down":
        vitesse_jeu = vitesses[-1] if vitesse_jeu == vitesses[0] else vitesses[vitesses.index(vitesse_jeu) - 1]
    bouton_Vitesse.config(image = vitesse_jeu[1])


def zoom_canvas(event):
    '''Zooms in or out of the canvas for better visability'''
    global Width, Height

    try:
        if event == "zoom in" or event.num == 4 or event.delta == 120: # Zoom In Canvas
            bouton_zoomout.config(state = "active")
            if Canvas.winfo_reqwidth() >= (field_frame.winfo_width() - 150) or Canvas.winfo_reqheight() >= (field_frame.winfo_height() - 150):
                Width, Height = Canvas.winfo_reqwidth(), Canvas.winfo_reqheight()
                bouton_zoomin.config(state = "disabled")
            else: 
                Width += 50; Height += 50
    except AttributeError: pass
    try:
        if event == "zoom out" or event.num == 5 or event.delta == -120: # Zoom Out Canvas
            bouton_zoomin.config(state = "active")
            if Canvas.winfo_reqwidth() <= nombre_case + 150 or Canvas.winfo_reqheight() <= nombre_case + 150:
                Width, Height = nombre_case + 100, nombre_case + 100
                bouton_zoomout.config(state = "disabled")
            else:
                Width -= 50; Height -= 50
    except AttributeError: pass

    canvas_refresh(); Canvas.configure(width = Width, height = Height)
    

def toggle_grid_lines():
    '''Toggles the grid lines of the Canvas'''
    global Grid_Line

    Grid_Line = grid_l_types[0] if Grid_Line == grid_l_types[-1] else grid_l_types[grid_l_types.index(Grid_Line) + 1] 
    Canvas.update(); canvas_refresh()


def change_field_size(*args):
    global field, fourmi_objs, nombre_case, pos, symbol, total_steps, refesh_counter

    nombre_case = int(cbox_field_taille.get()) + 1
    pos         = [nombre_case // 2,nombre_case // 2]
    field       = [["white" for _ in range(nombre_case)] for _ in range(nombre_case)]
    fourmi_objs = [{"sym" : 0, "pos" : [nombre_case // 2,nombre_case // 2], "direction" : directions[0], "case_actuelle" : "white", "couleur" : "red", "obj" : "None"}]
    symbol      = fourmi_objs[-1]["sym"] + 1 if fourmi_objs else 0
    cbox_field_taille.set(f"Taille Terrain: {cbox_field_taille.get()}x{cbox_field_taille.get()}")
    total_steps, refesh_counter = 0, 0
    label_steps.configure(text = f"Steps: {total_steps}")
    Main_Frame.focus() 
    canvas_refresh(); Canvas.update()


def del_fourmi(*args):
    global fourmi_objs
    
    fourmi_objs.remove(args[1])
    canvas_refresh(); Canvas.update()


def change_type_case(fourmi, y, x):
    '''Change la couleur de la case en fonction de sa couleur precedente'''
    global nombre_case

    if fourmi["case_actuelle"] == "white":
        field[y][x] = "black"
        Canvas.create_rectangle(x * (Height / nombre_case), y * (Width / nombre_case), (x + 1) * (Height / nombre_case), (y + 1) * (Width / nombre_case), outline = Grid_Line, fill = "black")
    else:
        field[y][x] = "white"
        Canvas.create_rectangle(x * (Height / nombre_case), y * (Width / nombre_case), (x + 1) * (Height / nombre_case), (y + 1) * (Width / nombre_case), outline = Grid_Line, fill = "white")


def fourmi_update():
    '''Met a jour le positionnement de la fourmi et les cases dans la liste "field" et canvas'''
    global directions, refesh_counter, total_steps, Grid_Line, Running
    
    if fourmi_objs:
        for ant in fourmi_objs:
            # Change la directionde la fourmi
            if ant["case_actuelle"] == "black": ant["direction"] = directions[-1] if ant["direction"] == directions[0]  else directions[directions.index(ant["direction"]) - 1]
            else:                               ant["direction"] = directions[0]  if ant["direction"] == directions[-1] else directions[directions.index(ant["direction"]) + 1]
        
            # Change la couleur de la case en fonction de sa couleur precedente 
            change_type_case(ant, *ant["pos"])

            # Bouge la fourmi en fonction de son orientation
            if   ant["direction"] == "0":   ant["pos"][0] = nombre_case - 1 if ant["pos"][0] == 0 else ant["pos"][0] - 1 # Up    | si pos y de ant est toute en haut elle redecnends tout en bas sinon elle monte d'une case
            elif ant["direction"] == "180": ant["pos"][0] = 0 if ant["pos"][0] == nombre_case - 1 else ant["pos"][0] + 1 # Down  | si pos y de ant est toute en bas elle remonte toute n haut sinon elle desends d'une case 
            elif ant["direction"] == "90":  ant["pos"][1] = 0 if ant["pos"][1] == nombre_case - 1 else ant["pos"][1] + 1 # Left  | si pos x de ant est toute a gauche elle repasse toute a droite sinon elle bouge d'une case vers la gauche
            elif ant["direction"] == "-90": ant["pos"][1] = nombre_case - 1 if ant["pos"][1] == 0 else ant["pos"][1] - 1 # Right | si pos x de ant est toute a droite elle repasse toute a gauche sinon elle bouge d'une case vers la droite

            # Met a jour le canvas et suvegarde la case actuelle
            ant["case_actuelle"] = field[ant["pos"][0]][ant["pos"][1]]
            ant["obj"] = Canvas.create_rectangle(ant["pos"][1] * (Height / nombre_case), ant["pos"][0] * (Width / nombre_case), (ant["pos"][1] + 1) * (Height / nombre_case), (ant["pos"][0] + 1) * (Width / nombre_case), outline = Grid_Line, fill = ant["couleur"])
            Canvas.tag_bind(ant["obj"],"<Button-3>", lambda x, fourmi = ant: del_fourmi(x, fourmi))
            Canvas.update()

        total_steps += 1; refesh_counter += 1
        if refesh_counter > 2000: canvas_refresh(); refesh_counter = 0
        label_steps.configure(text = f"Steps: {total_steps}")
    else: 
        Running = False
        bouton_Start.config(image = program_icons["Play"])
        return
    

def retour(*args):
    '''Fait retourner le jeu d'une unité de temps'''
    global directions, refesh_counter, total_steps, fourmi_objs
    
    if total_steps == 0 or not fourmi_objs: return
    else:
        for ant in fourmi_objs:
            
            if ant["case_actuelle"] == "black": Canvas.create_rectangle(ant["pos"][1] * (Height / nombre_case), ant["pos"][0] * (Width / nombre_case), (ant["pos"][1] + 1) * (Height / nombre_case), (ant["pos"][0] + 1) * (Width / nombre_case), outline = Grid_Line, fill = "black")
            else:                               Canvas.create_rectangle(ant["pos"][1] * (Height / nombre_case), ant["pos"][0] * (Width / nombre_case), (ant["pos"][1] + 1) * (Height / nombre_case), (ant["pos"][0] + 1) * (Width / nombre_case), outline = Grid_Line, fill = "white")

            if   ant["direction"] == "0"  : ant ["pos"][0] = 0 if ant ["pos"][0] == nombre_case - 1 else ant ["pos"][0] + 1 # Down
            elif ant["direction"] == "180": ant ["pos"][0] = nombre_case - 1 if ant ["pos"][0] == 0 else ant ["pos"][0] - 1 # Up
            elif ant["direction"] == "90" : ant ["pos"][1] = nombre_case - 1 if ant ["pos"][1] == 0 else ant ["pos"][1] - 1 # Left
            elif ant["direction"] == "-90": ant ["pos"][1] = 0 if ant ["pos"][1] == nombre_case - 1 else ant ["pos"][1] + 1 # Right

            ant["case_actuelle"] = field[ant["pos"][0]][ant["pos"][1]]
            change_type_case(ant, *ant["pos"])
            ant["case_actuelle"] = field[ant["pos"][0]][ant["pos"][1]]

            if ant["case_actuelle"] == "black": ant["direction"] = directions[0] if ant["direction"] == directions[-1] else directions[directions.index(ant["direction"]) + 1]
            else:                               ant["direction"] = directions[-1] if ant["direction"] == directions[0] else directions[directions.index(ant["direction"]) - 1]
                                    

            ant["obj"] = Canvas.create_rectangle(ant["pos"][1] * (Height / nombre_case), ant["pos"][0] * (Width / nombre_case), (ant["pos"][1] + 1) * (Height / nombre_case), (ant["pos"][0] + 1) * (Width / nombre_case), outline = Grid_Line, fill = ant["couleur"])
            Canvas.tag_bind(ant["obj"],"<Button-3>", lambda x, fourmi = ant: del_fourmi(x, fourmi))
            Canvas.update()  
        
        total_steps -= 1; refesh_counter += 1
        if refesh_counter > 2000: canvas_refresh(); refesh_counter = 0
        label_steps.configure(text = f"Steps: {total_steps}")


def canvas_refresh():
    '''Met a jour TOUT le canvas'''
    global fourmi_objs

    Canvas.delete("all")
    for y, line in enumerate(field):
        for x, cell in enumerate(line):
            Canvas.create_rectangle(x * (Height / nombre_case), y * (Width / nombre_case), (x + 1) * (Height / nombre_case), (y + 1) * (Width / nombre_case), outline = Grid_Line, fill = cell)
    for fourmi in fourmi_objs:
        fourmi["obj"] = Canvas.create_rectangle(fourmi["pos"][1] * (Height / nombre_case), fourmi["pos"][0] * (Width / nombre_case), (fourmi["pos"][1] + 1) * (Height / nombre_case), (fourmi["pos"][0] + 1) * (Width / nombre_case), outline = Grid_Line, fill = fourmi["couleur"])
        Canvas.tag_bind(fourmi["obj"],"<Button-3>", lambda x, fourmi = fourmi: del_fourmi(x, fourmi))


def reset_field(*args):
    '''Resets the field with the ants starting position'''
    global Running, field, fourmi_objs, refesh_counter

    pause()
    field = [["white" for _ in range(nombre_case)] for _ in range(nombre_case)]
    total_steps = 0
    for fourmi in fourmi_objs:
        fourmi["pos"] = [pos for pos in fourmi["start_pos"]]
        fourmi["direction"] = fourmi["start_direction"]
        fourmi["case_actuelle"] = field[fourmi["pos"][0]][fourmi["pos"][1]]
   
    refesh_counter = 0
    label_steps.config(text = f"Steps: {total_steps}")
    canvas_refresh()


def configure_creation_fourmi(*config_type):
    global symbol, pos, direction, fourmi_color, nombre_case, field, create_window
    
    if config_type:
        if config_type[0] == "color":
            fourmi_color = colorchooser.askcolor()[1]
            config_type[1].config(bg = fourmi_color, activebackground = fourmi_color)

        elif config_type[0] == "add":
            try: 
                if int(config_type[1].get()) > nombre_case or int(config_type[1].get()) < 0: pass
                else: pos[0] = int(config_type[1].get())
            except ValueError: pass
            try: 
                if int(config_type[2].get()) > nombre_case or int(config_type[2].get()) < 0: pass
                else: pos[1] = int(config_type[2].get())
            except ValueError: pass

            if not config_type[3].get(): pass
            else: direction = directions[directions.index(config_type[3].get())]
            

            fourmi_objs.append({"sym" : symbol, "pos" : pos, "start_pos" : pos, "direction" : direction, "start_direction" : direction, "case_actuelle" : field[pos[0]][pos[1]], "couleur" : fourmi_color, "obj" : "None"})
            config_type[4].destroy()
            symbol         = fourmi_objs[-1]["sym"] + 1 if fourmi_objs else 0
            pos            = [nombre_case // 2, nombre_case // 2]
            direction      = directions[0]
            fourmi_color  = "red"
            
            create_window = None
            canvas_refresh()
    else:
        create_window.destroy(); create_window = None


def ajout_fourmi(*args):
    '''Ouvre une fenetre separee pour configurer et ajouter une fourmi au terrain'''
    global fourmi_color, pos, nombre_case, directions, create_window

    pause()
    fourmi_create_window = tk.Tk()
    create_window = fourmi_create_window
    width, height = 900, 500
    fourmi_create_window.title("Configuration de la Fourmi")
    fourmi_create_window.geometry(f"{width}x{height}")
    fourmi_create_window.wm_attributes("-topmost", True)
    fourmi_create_window.eval("tk::PlaceWindow . center")
    fourmi_create_window.resizable(False,False)
    fourmi_create_window.protocol("WM_DELETE_WINDOW", lambda: configure_creation_fourmi())

    main_frame      = tk.Frame(fourmi_create_window, bg = "#1b1b1b", highlightbackground = "#3b3b3b", highlightthickness = 7)

    menu_creation    = tk.Frame(main_frame,      bg = "#1b1b1b")
    menu_bottom_bar  = tk.Frame(main_frame,      bg = "#1b1b1b")
    pos_frame        = tk.Frame(menu_creation,   bg = "#1b1b1b")
    pos_framel       = tk.Frame(pos_frame,       bg = "#1b1b1b")
    pos_framer       = tk.Frame(pos_frame,       bg = "#1b1b1b")
    color_frame      = tk.Frame(menu_creation,   bg = "#1b1b1b")
    color_framel     = tk.Frame(color_frame,     bg = "#1b1b1b")
    color_framer     = tk.Frame(color_frame,     bg = "#1b1b1b")
    direction_frame  = tk.Frame(menu_creation,   bg = "#1b1b1b")
    direction_framel = tk.Frame(direction_frame, bg = "#1b1b1b")
    direction_framer = tk.Frame(direction_frame, bg = "#1b1b1b")

    main_frame.pack       (side = None,     anchor = None,     fill = "both", expand = 1)
    menu_creation.pack    (side = None,     anchor = "center", fill = "both", expand = 1)
    menu_bottom_bar.pack  (side = None,     anchor = "s",      fill = "both", expand = 0)
    pos_frame.pack        (side = None,     anchor = "center", fill = "both", expand = 1, pady = 10)
    pos_framel.pack       (side = "left",   anchor = None,     fill = "x",    expand = 1,)
    pos_framer.pack       (side = "right",  anchor = None,     fill = "x",    expand = 1,)
    color_frame.pack      (side = None,     anchor = "center", fill = "both", expand = 1, pady = 10)
    color_framel.pack     (side = "left",   anchor = None,     fill = "x",    expand = 1,)
    color_framer.pack     (side = "right",  anchor = None,     fill = "x",    expand = 1,)
    direction_frame.pack  (side = None,     anchor = "center", fill = "both", expand = 1, pady = 10)
    direction_framel.pack (side = "left",   anchor = None,     fill = "x",    expand = 1,)
    direction_framer.pack (side = "right",  anchor = None,     fill = "x",    expand = 1,)


    position_label  = tk.Label     (pos_framel,       text = "Position Fourmi :",   font = ("Helvetica 25 bold"), fg = "white", bg = "#1b1b1b")
    direction_label = tk.Label     (direction_framel, text = "Direction Fourmi :",  font = ("Helvetica 25 bold"), fg = "white", bg = "#1b1b1b")
    couleur_label   = tk.Label     (color_framel,     text = "Couleur Fourmi :",                      font = ("Helvetica 25 bold"), fg = "white", bg = "#1b1b1b")
    posy_entry      = tk.Entry     (pos_framer,       cursor = "xterm", width = 10, font = ("Helvetica 15 bold"), fg = "white", bg = "#3b3b3b", relief = "flat", justify = "center", bd = 0)
    posx_entry      = tk.Entry     (pos_framer,       cursor = "xterm", width = 10, font = ("Helvetica 15 bold"), fg = "white", bg = "#3b3b3b", relief = "flat", justify = "center", bd = 0)
    direction_entry = ttk.Combobox (direction_framer, cursor = "hand2", text = "Position De La Fourmi:", font = ("Helvetica 10 bold"), state = "readonly",  justify = "center", values = directions)
    cancel          = tk.Button    (menu_bottom_bar,  cursor = "hand2", width = 8, height = 2, text = "Cancel", font = ("Helvetica 10 bold"), relief = "sunken", bd = 0, bg = "white",   activebackground = "red",         activeforeground = "black", command = lambda: configure_creation_fourmi())
    create          = tk.Button    (menu_bottom_bar,  cursor = "hand2", width = 8, height = 2, text = "Create", font = ("Helvetica 10 bold"), relief = "sunken", bd = 0, bg = "white",   activebackground = "light green", activeforeground = "black", command = lambda: configure_creation_fourmi("add", posy_entry, posx_entry, direction_entry, fourmi_create_window))
    couleur_box     = tk.Button    (color_framer,     cursor = "hand2", width = 6, height = 3, bg = fourmi_color,relief = "sunken", bd = 0, activebackground = fourmi_color, command = lambda: configure_creation_fourmi("color", couleur_box))

    position_label.pack  (side = "left",  padx = 30)
    posx_entry.pack      (side = "left",  fill = "x", expand = 1, ipady = 10)
    posy_entry.pack      (side = "right", fill = "x", expand = 1, ipady = 10, padx = 30)
    couleur_label.pack   (side = "left",  padx = 30)
    couleur_box.pack     (side = None,    anchor = "center", padx = 145)
    direction_label.pack (side = "left",  padx = 30)
    direction_entry.pack (side = None,    anchor = "center", padx = 100, ipady = 10, fill = "y", expand = 1)
    create.pack          (side = "right", anchor = None, padx = 5, pady = 3)
    cancel.pack          (side = "right", anchor = None, padx = 5, pady = 3)

    fourmi_create_window.mainloop()


# ========== Tkinter GUI ==========

racine.title("La Fourmi de Langton")
racine.iconphoto(True, program_icons["Logo"])
racine.state("zoomed")
racine.protocol("WM_DELETE_WINDOW", quitter)
racine.minsize(1870, 900)

# FRAMES CREATION:

Main_Frame      = tk.Frame (racine,       bg = "#1b1b1b", highlightbackground = "#3b3b3b", highlightthickness = 5)
menu_du_haut    = tk.Frame (Main_Frame,   bg = "#1b1b1b", highlightbackground = "#3b3b3b", highlightthickness = 5)
field_frame     = tk.Frame (Main_Frame,   bg = "#1b1b1b", highlightbackground = "#3b3b3b", highlightthickness = 5)
separator_frame = tk.Frame (menu_du_haut, bg = "#1b1b1b")

# FRAMES PACK:

Main_Frame.pack   (anchor = "center", fill = "both", expand = 1)
menu_du_haut.pack (anchor = "n",      fill = "x",    expand = 0)
field_frame.pack  (anchor = "s",      fill = "both", expand = 1)


# BOUTTONS/LABEL CREATION:

bouton_Start           = tk.Button    (menu_du_haut, image = program_icons["Play"],      relief = "sunken", bd = 0, cursor = "hand2", bg = "light green",  activebackground = "dark green",  command = start)
bouton_Retour          = tk.Button    (menu_du_haut, image = program_icons["Backwards"], relief = "sunken", bd = 0, cursor = "hand2", bg = "cyan",         activebackground = "dark cyan",   command = retour)
bouton_Avancer         = tk.Button    (menu_du_haut, image = program_icons["Forwards"],  relief = "sunken", bd = 0, cursor = "hand2", bg = "cyan",         activebackground = "dark cyan",   command = avancer)
bouton_Vitesse         = tk.Button    (menu_du_haut, image = program_icons["Speed 1"],   relief = "sunken", bd = 0, cursor = "hand2", bg = "magenta",      activebackground = "purple",      text = "Vitesse ",         compound = "right",font = ("Impact 20"), command = changer_vitesse)
bouton_ajout_fourmi   = tk.Button     (menu_du_haut, image = program_icons["Add Ant"],   relief = "sunken", bd = 0, cursor = "hand2", bg = "light yellow", activebackground = "yellow",      text = "  Ajout fourmi  ", compound = "left", font = ("Impact 20"), command = ajout_fourmi)
bouton_zoomin          = tk.Button    (menu_du_haut, image = program_icons["Zoom In"],   relief = "sunken", bd = 0, cursor = "hand2", bg = "white",        activebackground = "white",       command = lambda a = "zoom in" : zoom_canvas(a))
bouton_zoomout         = tk.Button    (menu_du_haut, image = program_icons["Zoom Out"],  relief = "sunken", bd = 0, cursor = "hand2", bg = "white",        activebackground = "white",       command = lambda a = "zoom out": zoom_canvas(a))
bouton_Charger         = tk.Button    (menu_du_haut, image = program_icons["Load"],      relief = "sunken", bd = 0, cursor = "hand2", bg = "orange",       activebackground = "orange",      command = charger)
bouton_Sauvegarder     = tk.Button    (menu_du_haut, image = program_icons["Save"],      relief = "sunken", bd = 0, cursor = "hand2", bg = "orange",       activebackground = "orange",      command = sauvegarder)
bouton_Quitter         = tk.Button    (menu_du_haut, image = program_icons["Escape"],    relief = "sunken", bd = 0, cursor = "hand2", bg = "red",          activebackground = "dark red",    command = quitter)
cbox_field_taille      = ttk.Combobox (menu_du_haut, text = "Choisie la taille",         justify = "center", values = taille_grille, font = ("Impact 25"), state = "readonly")
label_steps            = tk.Label     (field_frame,  text =  f"Step: {total_steps}",     font = ("Impact 18"), fg = "white",   bg = "#2b2b2b")

# BOUTTONS/LABEL PACK:

bouton_Start.pack          (side = "left",  padx = 10, pady = 10, ipadx = 5, ipady = 5, expand = 1)
bouton_Retour.pack         (side = "left",  padx = 10, pady = 10, ipadx = 5, ipady = 5, expand = 0)
bouton_Avancer.pack        (side = "left",  padx = 10, pady = 10, ipadx = 5, ipady = 5, expand = 0)
bouton_Vitesse.pack        (side = "left",  padx = 10, pady = 10, ipadx = 5, ipady = 5, expand = 1)
bouton_ajout_fourmi.pack   (side = "left",  padx = 10, pady = 10, ipadx = 5, ipady = 5, expand = 1, anchor = "center")
bouton_zoomin.pack         (side = "left",  padx = 10, pady = 10, ipadx = 5, ipady = 5, expand = 0)
bouton_zoomout.pack        (side = "left",  padx = 10, pady = 10, ipadx = 5, ipady = 5, expand = 0)
cbox_field_taille.pack     (side = "left",  padx = 10, pady = 10, ipadx = 5, ipady = 15, expand = 0)
separator_frame.pack       (side = "left",  expand = 1, fill = "both")
bouton_Quitter.pack        (side = "right", padx = 10, pady = 10, ipadx = 5, ipady = 5, expand = 1, anchor = "e")
bouton_Sauvegarder.pack    (side = "right", padx = 10, pady = 10, ipadx = 5, ipady = 5, expand = 0)
bouton_Charger.pack        (side = "right", padx = 10, pady = 10, ipadx = 5, ipady = 5, expand = 0)
cbox_field_taille.set      (f"Taille Terrain: {nombre_case - 1}x{nombre_case - 1}")
label_steps.place          (x = 10, y = 10)

# CANVAS CREATION / PACK:

Canvas = tk.Canvas(field_frame, height = Height, width = Width, highlightthickness = 0, bg = "#1b1b1b")
Canvas.pack(expand = 1, anchor = "center")
canvas_refresh() # Affiche le canvas pour la premiere fois

# ========== Raccourcis Clavier ==========

racine.bind("<Up>",         changer_vitesse)
racine.bind("<Down>",       changer_vitesse)
racine.bind("<Right>",      avancer)
racine.bind("<Left>",       retour)
racine.bind("<space>",      start)
racine.bind('<Escape>',     quitter)
racine.bind("<KeyPress>",   tk_key_control)
racine.bind("<Control-s>",  sauvegarder)
racine.bind("<Control-l>",  charger)
racine.bind("<MouseWheel>", zoom_canvas)
racine.bind("<BackSpace>",  reset_field)
cbox_field_taille.bind("<<ComboboxSelected>>", change_field_size)

racine.mainloop()

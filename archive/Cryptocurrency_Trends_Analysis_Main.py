#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  7 09:29:40 2024

@author: komalwavhal
""" 
 
import tkinter.scrolledtext as tkscrolled
import os
import tkinter as tk
from tkinter import ttk
from tkinter import *
import tkinter.scrolledtext as tkscrolled
from PIL import Image,ImageTk
from tkinter.filedialog import askopenfilename
import threading
from time import sleep 
import subprocess
import time
import sys
import tkinter, sys
from tkinter import scrolledtext
#try:
#    import docx
#except:
#    os.system('python -m pip install -i python-docx')
#    import docx
   
from tkinter import messagebox   
import time
from pathlib import Path   
from tkinter import filedialog
import io
import threading     
import tkinter as tk  
from tkinter import messagebox
from PIL import Image, ImageTk    
from tkinter import messagebox as msg   
import datetime
from tkinter import ttk 
import tkinter as tk
#import Config
import tkinter as tk
from tkinter import ttk
import shutil
from datetime import datetime
#from win32com.shell import shell, shellcon
LARGEFONT =("Verdana", 35)
from AppKit import NSWorkspace
import getpass 
# import win32gui, win32con 
import time 



class tkinterApp(tk.Tk):
    
    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
    
        
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)
        
        # creating a container
        container = tk.Frame(self)
        container.pack(side = "top", fill = "both", expand = True)
        
        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)
        
        self.frames = {} 
        
        for F in (StartPage, Page1): 
            frame = F(container, self)  
            self.frames[F] = frame 
            frame.grid(row = 0, column = 0, sticky ="nsew")
            
        self.show_frame(StartPage)
    
    # to display the current frame passed as  parameter
    def show_frame(self, cont): 
    
        frame = self.frames[cont]
        frame.tkraise() 
           
        import os
        try:
            ### for Windows users
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            print(desktop)
            Parent_Folder_Path = desktop + "/BIA_660_Project_Repository"
            print(Parent_Folder_Path)
        
        except: 
            ### for Mac users
            desktop = os.path.expanduser("~/Desktop")
            desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
            Parent_Folder_Path = desktop + "/BIA_660_Project_Repository"
            print(Parent_Folder_Path)
            
        Parent_Folder_Path = Parent_Folder_Path
         
         
        import getpass 
        user = str(getpass.getuser() )
        newpath = Parent_Folder_Path + "\Input\\" + user  
        if not os.path.exists(newpath):
        	os.makedirs(newpath)
        

# first window frame startpage 
class StartPage(tk.Frame):
 
 
    
	def __init__(self, parent, controller): 
        
		win_user = 0
		import os
		try:
            ### for Windows users
		    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
		    print(desktop)
		    Parent_Folder_Path = desktop + "/BIA_660_Project_Repository"
		    print(Parent_Folder_Path)
        
		except: 
		    win_user = 1            
            ### for Mac users
		    desktop = os.path.expanduser("~/Desktop")
		    desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
		    Parent_Folder_Path = desktop + "/BIA_660_Project_Repository"
		    print(Parent_Folder_Path)
            
		Parent_Folder_Path = Parent_Folder_Path
         
		if win_user == 0:		 
		    Img_Path = Parent_Folder_Path + '\\Images'      
		    userManual_Button_imgFilePath = (Img_Path+ "\\UserManual.png") 
		    imgFilePath =  (Img_Path+ "\\Background_Image.png")  
		    AFFIRM_ICON_imgFilePath =   (Img_Path+ "\\AFFIRM_ICON.png")
		    userManual_Button_imgFilePath = (Img_Path+ "\\UserManual.png") 
        
		else:
		    Img_Path = Parent_Folder_Path + '//Images'     
		    userManual_Button_imgFilePath = (Img_Path+ "//UserManual.png") 
		    imgFilePath =  (Img_Path+ "//Background_Image.png")  
		    AFFIRM_ICON_imgFilePath =   (Img_Path+ "//AFFIRM_ICON.png")
		    userManual_Button_imgFilePath = (Img_Path+ "//UserManual.png") 
            
		print('Img_Path',Img_Path)
 

		tk.Frame.__init__(self, parent)
		          
		 
		##Background Image 
		img = Image.open(imgFilePath)

		photo = ImageTk.PhotoImage(img)
		lab1 = ttk.Label(self,image=photo)
		lab1.pack()
		lab1.place(x=0)
		lab1.image = photo        

        #####AFFIRM_ICON_imgFilePath   Button
		AFFIRM__Button_image = Image.open(AFFIRM_ICON_imgFilePath) 
		photo = ImageTk.PhotoImage(AFFIRM__Button_image)        
		button_Export = tk.Button(self,image=photo,command= lambda : controller.show_frame(Page1))  ###,bg = "white", bd = 0
		button_Export.place(x=1080,y=370)        
		button_Export.image = photo  
         
		self.configure(background='#FFFFFF')

# second window frame page1
class Page1(tk.Frame):
      
     
    def Clear_Logs(self) :
        self.text.config(state='normal')
        self.text.delete("1.0" , "end")
         
	 
    def domain_changed_1(self,event):
            
       
            self.domainselected_112.config(state='disabled')
            self.domainselected_122.config(state='disabled')
            self.domainselected_1.config(state='disabled')
            
            
            self.mainGetData_1 = list()
            self.mainGetData_1.append(self.domainselected_1.get())
		 	 
    def domain_changed_12(self,event):
        
       
            self.domainselected_112.config(state='disabled')
            self.domainselected_122.config(state='disabled')
            self.domainselected_1.config(state='normal')
    
            
            self.mainGetData_12 = list()
            self.mainGetData_12.append(self.domainselected_12.get())
		 	 
	 
    
 
    ################ year range selection  
    
    def domain_changed_112(self,event):
        
        self.domainselected_1.config(state='disabled')
        self.domainselected_12.config(state='disabled')
        self.domainselected_122.config(state='normal')
        
        self.mainGetData_112 = list()
        self.mainGetData_112.append(self.domainselected_112.get())
		 	 
    def domain_changed_122(self,event):
        
        self.domainselected_1.config(state='disabled')
        self.domainselected_12.config(state='disabled')
    
        self.mainGetData_122 = list()
        self.mainGetData_122.append(self.domainselected_122.get())
    		 	  


    def update_dropdown_state(self):
        """Enable or disable the dropdown based on the radiobutton selection."""
        if self.selected_month.get() == 1:  # "Enable Dropdown" is selected 
            self.domainselected_1.config(state='disabled')
            self.domainselected_12.config(state='normal')
            self.domainselected_112.config(state='disabled')
            self.domainselected_122.config(state='disabled')
            self.domainselected_112.set('') 
            self.domainselected_122.set('')
            
        elif self.selected_month.get() == 2:  # "Disable Dropdown" is selected
              
            self.domainselected_1.config(state='disabled')
            self.domainselected_12.config(state='disabled')
            self.domainselected_112.config(state='normal')
            self.domainselected_122.config(state='disabled')
            self.domainselected_1.set('') 
            self.domainselected_12.set('')

    
    
    def minimize_all_windows(self):
        # Get the list of all currently running applications
        workspace = NSWorkspace.sharedWorkspace()
        apps = workspace.runningApplications()
        
        for app in apps:
            if app.isActive():
                # Minimize the app window
                app.hide()  # This hides the app, essentially minimizing it
    
    
    
    def clear_fields(self):
        
        
        self.domainselected_1.set('') 
        self.domainselected_12.set('')
        self.domainselected_112.set('') 
        self.domainselected_122.set('')

        if self.selected_month.get() == 2:  # "Enable Dropdown" is selected 
            self.domainselected_1.config(state='disabled')
            self.domainselected_12.config(state='disabled')
            
        if self.selected_month.get() == 1:  # "Enable Dropdown" is selected 
            self.domainselected_112.config(state='disabled')
            self.domainselected_122.config(state='disabled')
        


    def __init__(self, parent, controller):
         
        win_user = 0
        
        import os
        try:
            ### for Windows users
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            print(desktop)
            Parent_Folder_Path = desktop + "/BIA_660_Project_Repository"
            print(Parent_Folder_Path)
            Img_Path = Parent_Folder_Path + '\\Images'  
            imgFilePath =  (Img_Path+"\\Main_Page1.png") 
            Bck_Button_imgFilePath = (Img_Path+'\\Bck_Button.png') 
            run_Button_imgFilePath = (Img_Path+'\\run.PNG')
            pdf_image = Image.open(Img_Path+'\\PDF_ICON.png') 
        except: 
            win_user = 1            
            ### for Mac users
            desktop = os.path.expanduser("~/Desktop")
            desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
            Parent_Folder_Path = desktop + "/BIA_660_Project_Repository"
            print(Parent_Folder_Path)
            Img_Path = Parent_Folder_Path + '//Images'  
            imgFilePath =  (Img_Path+"//Main_Page1.png") 
            Bck_Button_imgFilePath = (Img_Path+'//Bck_Button.png') 
            run_Button_imgFilePath = (Img_Path+'//run.PNG')
            pdf_image = (Img_Path+'//PDF_ICON.png') 
          
          
        Parent_Folder_Path = Parent_Folder_Path
        
        tk.Frame.__init__(self, parent)
         
        ##Background Image 
        
        img = Image.open(imgFilePath)
        
        photo = ImageTk.PhotoImage(img)
        lab1 = ttk.Label(self,image=photo)
        lab1.pack()
        lab1.place(x=0)
        lab1.image = photo           
         
    
        #####Back Button
        Bck_Button_image = Image.open(Bck_Button_imgFilePath) 
        photo = ImageTk.PhotoImage(Bck_Button_image)        
        button_Export = tk.Button(self,image=photo,command= lambda : controller.show_frame(StartPage))  ###,bg = "white", bd = 0
        button_Export.place(x=23,y=15)        
        button_Export.image = photo  
         
        
        self.configure(background='#FFFFFF') 
       
        # #### ----------###(Application Logs)---------------------------------- 
        # self.text = scrolledtext.ScrolledText(self,wrap = WORD,bg = '#FFFFFF',height=13, width=105, font=('calibri',12),relief= 'ridge') 
        # self.text.place(x=230,y=360)
        
        # self.configure(background='#FFFFFF') 
          
           
        ###------------------Select radio button -----------------------------------------------------------------------
 
    
        self.selected_month  = tk.IntVar()
#        self.selected_month.set(1)
        self.t = tk.Radiobutton(self,text='', value=1,variable = self.selected_month,command=self.update_dropdown_state ,fg= 'green', bg = '#FFFFFF',font=('calibri',10,'bold') )
        self.t.place(x=360,y=116)  
#        self.t.config(state=DISABLED)
		 
        self.m = tk.Radiobutton(self,text='', value=2,variable = self.selected_month,command=self.update_dropdown_state ,fg= 'green', bg = '#FFFFFF',font=('calibri',10,'bold') )
        self.m.place(x=360,y=180) 
#        self.m.config(state=DISABLED)    
    
        ###-----------------------------------------------------------------------------------------
              
        
        ##-----------------------Dropdown Button    -------------------------------------------------------------------------
          
        #######Dropdown Button   - for years
        tkvar_12 = tk.StringVar()  
        self.domainselected_12 = ttk.Combobox(self,background = "#FFFFFF",foreground= 'black', width = 14, font=('Times',14),textvariable = tkvar_12)
         
        from datetime import datetime

        # Get the current year
        current_year = datetime.now().year

        # Generate the list of years from 2010 to the current year
        years = list(range(2010, current_year + 1))

        # Add 'Select option' at the beginning of the list
        years_with_select = ['Select option'] + years

        # Convert the list to a tuple and print
        years_with_select_tuple = tuple(years_with_select)
        print(years_with_select_tuple)

        ##------------------------------------------------------------------------------------------------
        
        # Adding combobox drop down list for year 
        self.domainselected_12['values'] = years_with_select_tuple
        self.domainselected_12['state'] = 'readonly'
        self.domainselected_12.grid(row = 4, column = 7)
        self.domainselected_12.place(x=470,y=116)         
        self.domainselected_12.bind('<<ComboboxSelected>>', self.domain_changed_12)           

        ###----------------------------------------------------------------------------------------------------------------
 
        ##-----------------------Dropdown Button    -------------------------------------------------------------------------
          
        #######Dropdown Button   - for months
        tkvar_1 = tk.StringVar()  
        self.domainselected_1 = ttk.Combobox(self,background = "#FFFFFF",foreground= 'black', width = 14, font=('Times',14),textvariable = tkvar_1)
         
        # Adding combobox drop down list for month 
        self.domainselected_1['values'] = ('Select option',
                                   'January',
                                   'February',
                                   'March',
                                   'April',
                                   'May',
                                   'June',
                                   'July',
                                   'August',
                                   'September',
                                   'October',
                                   'November',
                                   'December')  
        self.domainselected_1['state'] = 'readonly'
        self.domainselected_1.grid(row = 4, column = 7)
        self.domainselected_1.place(x=670,y=116)         
        self.domainselected_1.bind('<<ComboboxSelected>>', self.domain_changed_1)           
 
           
        ###----------------------------------------------------------------------------------------------------------------
 
        ##-----------------------Dropdown Button  for range of years selection  -------------------------------------------------------------------------

        ##-----------------------Dropdown Button    -------------------------------------------------------------------------
          
        #######Dropdown Button   - for start year
        tkvar_112 = tk.StringVar()  
        self.domainselected_112 = ttk.Combobox(self,background = "#FFFFFF",foreground= 'black', width = 14, font=('Times',14),textvariable = tkvar_112)
         
        from datetime import datetime

        # Get the current year
        current_year = datetime.now().year

        # Generate the list of years from 2010 to the current year
        years = list(range(2010, current_year + 1))

        # Add 'Select option' at the beginning of the list
        years_with_select = ['Select option'] + years

        # Convert the list to a tuple and print
        years_with_select_tuple = tuple(years_with_select)
        print(years_with_select_tuple)

        
        # Adding combobox drop down list for year 
        self.domainselected_112['values'] = years_with_select_tuple
        self.domainselected_112['state'] = 'readonly'
        self.domainselected_112.grid(row = 4, column = 7)
        self.domainselected_112.place(x=470,y=180)         
        self.domainselected_112.bind('<<ComboboxSelected>>', self.domain_changed_112)           

        ###----------------------------------------------------------------------------------------------------------------
 

    
        ##-----------------------Dropdown Button    -------------------------------------------------------------------------
          
        #######Dropdown Button   - for end year
        tkvar_122 = tk.StringVar()  
        self.domainselected_122 = ttk.Combobox(self,background = "#FFFFFF",foreground= 'black', width = 14, font=('Times',14),textvariable = tkvar_122)
         
        from datetime import datetime

        # Get the current year
        current_year = datetime.now().year

        # Generate the list of years from 2010 to the current year
        years = list(range(2010, current_year + 1))

        # Add 'Select option' at the beginning of the list
        years_with_select = ['Select option'] + years

        # Convert the list to a tuple and print
        years_with_select_tuple = tuple(years_with_select)
        print(years_with_select_tuple)

        
        ##------------------------------------------------------------------------------------------------
        

        # Adding combobox drop down list for year 
        self.domainselected_122['values'] = years_with_select_tuple
        self.domainselected_122['state'] = 'readonly'
        self.domainselected_122.grid(row = 4, column = 7)
        self.domainselected_122.place(x=670,y=180)         
        self.domainselected_122.bind('<<ComboboxSelected>>', self.domain_changed_122)   
        
        ###----------------------------------------------------------------------------------------------------------------
   
        # Clear button
        self.clear_button = tk.Button(self,background = "#FFFFFF", text="Clear Date Selection", command=self.clear_fields, fg='red', bg='#FFFFFF', font=('Times',14), width=15)
        self.clear_button.place(x=820, y=146)
  
        ###----------------------------------------------------------------------------------------------------------------
        
        self.domainselected_112.config(state='disabled')
        self.domainselected_122.config(state='disabled')
         
        self.domainselected_1.config(state='disabled')
        self.domainselected_12.config(state='disabled') 


        ###----------------------------------------------------------------------------------------------------------------
        
     
        ###------------------Select radio button for crypto currency-----------------------------------------------------------------------
  
        self.selected_crypto  = tk.IntVar() 
        
        self.t = tk.Radiobutton(self,text='BTC', value=1,variable = self.selected_crypto,command=self.update_dropdown_state ,fg= 'Black', bg = '#FFFFFF',font=('calibri',15,'bold'),    width=8  )     
        self.t.place(x=360,y=266)  
        
        self.t = tk.Radiobutton(self,text='Ethereum', value=2,variable = self.selected_crypto,command=self.update_dropdown_state ,fg= 'Black', bg = '#FFFFFF',font=('calibri',15,'bold') ,    width=8  )     
        self.t.place(x=400+87,y=266)  
        
        self.t = tk.Radiobutton(self,text='Binance', value=3,variable = self.selected_crypto,command=self.update_dropdown_state ,fg= 'Black', bg = '#FFFFFF',font=('calibri',15,'bold') ,    width=8  )     
        self.t.place(x=440+175,y=266)  
        
        self.t = tk.Radiobutton(self,text='Solana', value=4,variable = self.selected_crypto,command=self.update_dropdown_state ,fg= 'Black', bg = '#FFFFFF',font=('calibri',15,'bold') ,    width=8  )     
        self.t.place(x=480+270,y=266) 
        
        self.t = tk.Radiobutton(self,text='USD Coin', value=5,variable = self.selected_crypto,command=self.update_dropdown_state ,fg= 'Black', bg = '#FFFFFF',font=('calibri',15,'bold') ,    width=8  )     
        self.t.place(x=520+360,y=266)  
        
        self.t = tk.Radiobutton(self,text='Ripple', value=6,variable = self.selected_crypto,command=self.update_dropdown_state ,fg= 'Black', bg = '#FFFFFF',font=('calibri',15,'bold') ,    width=8  )     
        self.t.place(x=360,y=316)  
        
        self.t = tk.Radiobutton(self,text='StETH', value=7,variable = self.selected_crypto,command=self.update_dropdown_state ,fg= 'Black', bg = '#FFFFFF',font=('calibri',15,'bold') ,    width=8  )     
        self.t.place(x=400+87,y=316)  
        
        self.t = tk.Radiobutton(self,text='Dogecoin', value=8,variable = self.selected_crypto,command=self.update_dropdown_state ,fg= 'Black', bg = '#FFFFFF',font=('calibri',15,'bold') ,    width=8  )     
        self.t.place(x=440+175,y=316)  
        
        self.t = tk.Radiobutton(self,text='TRON', value=9,variable = self.selected_crypto,command=self.update_dropdown_state ,fg= 'Black', bg = '#FFFFFF',font=('calibri',15,'bold') ,    width=8  )     
        self.t.place(x=480+270,y=316)  
        
        self.t = tk.Radiobutton(self,text='Tether', value=10,variable = self.selected_crypto,command=self.update_dropdown_state ,fg= 'Black', bg = '#FFFFFF',font=('calibri',15,'bold') ,    width=8  )     
        self.t.place(x=520+360,y=316)  
        
 
        ###------------------Select radio button for crypto currency -----------------------------------------------------------------------
  

        #####RUN Automatoin  
        runCryptocurrency_image = Image.open(run_Button_imgFilePath) 
        photo = ImageTk.PhotoImage(runCryptocurrency_image)        
        button_Export = tk.Button(self,image=photo,command=  self.Execute_BIA_Crypto)  ###,bg = "white", bd = 0
        button_Export.place(x=587,y=360)        
        button_Export.image = photo  
         
        
        self.configure(background='#FFFFFF')     


    def Execute_BIA_Crypto(self) :  
        # run process in a thread to avoid blocking gui 
        t = threading.Thread(target=self.execute_main_threde)
        t.start()
        
    def execute_main_threde(self) :  
        # run process in a thread to avoid blocking gui 
        t = threading.Thread(target=self.execute_main)
        t.start()

    # def show_error_message(self, title, message):
    #     """Display the error message box."""
    #     messagebox.showerror(title, message )

    def show_error_message(self, title, message):
        """Display a custom error message box without an icon."""
        # Create a custom Toplevel window for the error message box
        error_window = tk.Toplevel(self)
        error_window.title("Terminating Execution")
        error_window.geometry("400x200")  # You can adjust the size
        
        # Add a label with the error message
        error_message = "Error occurred while running Cryptocurrency Trends Analysis Platform - please enter valid details in Application GUI"
        message_label = tk.Label(error_window, text=error_message, fg="black", bg = '#FFFFFF', font=('calibri',15,'bold') , wraplength=350)
        message_label.pack(pady=40)

        error_window.configure(background='#FFFFFF') 
        
        # Add a button to close the error window
        close_button = tk.Button(error_window, text="OK", command=error_window.destroy)
        close_button.pack()
        
         
    def execute_main(self):  
        
        self.minimize_all_windows()
        
        import getpass 
        user = str(getpass.getuser() ) 
              
        year_for_month_Selection = "" 
        month_Selection = "" 
        start_year_for_range_Selection = ""
        end_year_for_range_Selection = ""
        radio_val_month_year_range_selection = ""
        radio_val_selected_crypto_selection = ""
        
        import datetime
        now = datetime.datetime.now() 
        x = str(now.strftime("%Y-%m-%d %H:%M:%S"))   
        time.sleep(1)   
       
        #######################################################################################
               
        radio_val_month_year_range_selection = self.selected_month.get()  
        
        
        if (radio_val_month_year_range_selection == 0)  :
            title="Terminating Execution", 
            message="Error occurred while running Cryptocurrency Trends Analysis Platform - please enter valid details in Application GUI"
 
            self.show_error_message(title, message)
        else:
            
            print('radio_val_month_year_range_selection - ', radio_val_month_year_range_selection) 
            
            
        #######################################################################################

           
            
        try:
            year_for_month_Selection = self.domainselected_1.get()
        except: 
            year_for_month_Selection = 'Select option'
             
        try:
            month_Selection = self.domainselected_12.get()
        except: 
            month_Selection = 'Select option'
             
        try:
            start_year_for_range_Selection = self.domainselected_112.get()
        except: 
            start_year_for_range_Selection = 'Select option'
         
        try:
            end_year_for_range_Selection = self.domainselected_122.get()
        except: 
            end_year_for_range_Selection = 'Select option'
           
         
        #######################################################################################
        
        # if (year_for_month_Selection == ' ') or (year_for_month_Selection == 'Select option') :
        #     print('check next ')
            
        # elif (end_year_for_range_Selection == ' ') or (end_year_for_range_Selection == 'Select option')  :
        #     print('check next ')
            
        # elif (month_Selection == ' ') or (month_Selection == 'Select option') :
        #     print('check next ')
            
        # elif (start_year_for_range_Selection == ' ') or (start_year_for_range_Selection == 'Select option') :
        #     print('check next ')
            
        # else:
            
        #     title="Terminating Execution", 
        #     message="Error occurred while running Cryptocurrency Trends Analysis Platform - please enter valid details in Application GUI"
 
        #     self.show_error_message(title, message)
     
        
        #######################################################################################
        
        start_year_for_range_Selection = int(start_year_for_range_Selection)
        end_year_for_range_Selection = int(end_year_for_range_Selection)

        print('year_for_month_Selection - ', year_for_month_Selection)
        print('month_Selection - ', month_Selection)
        print('start_year_for_range_Selection - ', start_year_for_range_Selection)
        print('end_year_for_range_Selection - ', end_year_for_range_Selection)
        
         
        #######################################################################################
            
        radio_val_selected_crypto_selection = self.selected_crypto.get()  
        print('radio_val_selected_crypto_selection',radio_val_selected_crypto_selection)
        
        #######################################################################################
        
        if not(radio_val_selected_crypto_selection == 1 ) and not (radio_val_selected_crypto_selection  == 2  ) and not (radio_val_selected_crypto_selection   == 3 ) and not (radio_val_selected_crypto_selection    == 4  ) and not (radio_val_selected_crypto_selection   == 5 ) and not  (radio_val_selected_crypto_selection  == 6  ) and not (radio_val_selected_crypto_selection    == 7  ) and not  (radio_val_selected_crypto_selection    == 8  ) and not (radio_val_selected_crypto_selection     == 9 ) and  not(radio_val_selected_crypto_selection   == 10   )  :
            title="Terminating Execution", 
            message="Error occurred while running Cryptocurrency Trends Analysis Platform - please select the Cryptocurrency name in Application GUI"
 
            self.show_error_message(title, message)
        else:
            
            print('radio_val_selected_crypto_selection - ', radio_val_selected_crypto_selection) 
            
        
        ############ (Import Custom Libraries) ##################################

        #### --(Importing Custom Libraries for downloading the Google News Data)--------------------------------  
 
        from CryptoData_Google_News import CryptoData_Google_News
  
        #### --(Initializing Data Processing Class Object)------------------------------------------------------- 

        objCryptoData_Google_News = CryptoData_Google_News()
        
        
        if (radio_val_selected_crypto_selection == 1 ):
            crypto_name = 'BTC'  
        if (radio_val_selected_crypto_selection == 2 ):
            crypto_name = "Ethereum" 
        if (radio_val_selected_crypto_selection == 3 ):
            crypto_name = "Binance" 
        if (radio_val_selected_crypto_selection == 4 ):
            crypto_name = "Solana"   
        if (radio_val_selected_crypto_selection == 5 ):
            crypto_name = "usdcoin" 
        if (radio_val_selected_crypto_selection == 6 ):
            crypto_name = "Ripple"  
        if (radio_val_selected_crypto_selection == 7 ):
            crypto_name = "StETH"   
        if (radio_val_selected_crypto_selection == 8 ):
            crypto_name = "Dogecoin"   
        if (radio_val_selected_crypto_selection == 9 ):
            crypto_name = "TRON"   
        if (radio_val_selected_crypto_selection == 10 ):
            crypto_name = "Tether"   


        #######################################################################################
        
        if radio_val_month_year_range_selection == 2 :
                  
            objCryptoData_Google_News.GoogleNews_Data(crypto_name, start_year_for_range_Selection, end_year_for_range_Selection)
         
        #######################################################################################
                
        
            
        
      #   #######################################################################################
        
      #   dropdown_value_year_month_selection = ''
      #   dropdown_value_month_selection = ''
      #   dropdown_value_year_start_range_selection = ''
      #   dropdown_value_year_end_range_selection = ''
        
      #   #######################################################################################
        
      #   try:
      #       dropdown_value_year_month_selection = self.mainGetData_1[0]
      #   except: 
      #       dropdown_value_year_month_selection = 'No Value selected'
             
      #   try:
      #       dropdown_value_month_selection = self.mainGetData_12[0]
      #   except: 
      #       dropdown_value_month_selection = 'No Value selected'
            
      #   try:
      #       dropdown_value_year_start_range_selection = self.mainGetData_112[0]
      #   except: 
      #       dropdown_value_year_start_range_selection = 'No Value selected'
            
      #   try:
      #       dropdown_value_year_end_range_selection  = self.mainGetData_122[0]
      #   except: 
      #       dropdown_value_year_end_range_selection = 'No Value selected'
            
    
              
      # #######################################################################################
      
      
      #   if (UserName =="")  :
             
      #       flag = 0
      #       self.display_text('>>> Error occoured while running Cryptocurrency Trends Analysis Platform ' + '\n'  , 'Error')  
             
      #       self.display_text('>>> please enter valid details in Application GUI' + '\n'  , 'Error')
      #       self.display_text('>>> Terminating Execution' + '\n'  , 'Error')  
      #       self.text.config(state='disabled') 
      #       stopcodehere
 
 

time.sleep(1)     
root = tkinterApp()

############################################################################
 
#root = tk.Tk()
root.title("Cryptocurrency Trends Analysis Platform (Version: 1.0.0)")
root.geometry('1390x770')

root.pack_propagate(0)
root.resizable(0,0)

def OnFocusIn(event):
    if type(event.widget).__name__ == 'Cryptocurrency Trends Analysis Platform (Version: 1.0.0)':
        event.widget.attributes('-topmost', False)

# root.attributes('-topmost', True)
# root.focus_force()
# root.bind('<FocusIn>', OnFocusIn)

root.mainloop()

     



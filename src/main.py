import copy
import os
import time
from tkinter import *
from tkinter import font
from tkinter import simpledialog
import image_registration
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pypylon
from PIL import ImageTk, Image
from aux_functions import *
from matplotlib import cm

# settings
cam_number = 0
exposure_time = 50000  # range(10;1e6)


class DICGUI:

    def __init__(self, master):
        self.master = master

        # initial variables
        # geometry
        self.cam_width = 2590
        self.cam_height = 2048
        self.ratio_width_dic, self.ratio_height_dic = 2.5, 2.1
        self.ratio_width_plot, self.ratio_height_plot = 4.5, 4

        self.gui_width = int(self.cam_width / 1.5)
        self.gui_height = int(self.cam_height / 2)
        master.geometry(str(self.gui_width) + 'x' + str(self.gui_height))

        # version
        self.version = 1.1

        # camera settings
        self.def_cam_dic = 0
        self.x, self.y = [], []
        self.scale = 1

        # extensometer variables
        self.extensometer_list, self.extensometer_possitions, self.extensometer_lenghts, self.extensometer_lenghts_new = [], [], [], [],
        self.actual_extensometer = -1

        # DIC variables
        self.dic_started = False
        self.x_extensions, self.y_extensions, self.tot_extensions, self.saved_dx, self.saved_dy = [], [], [], [], []
        self.time = [0]
        self.ref_image, self.cur_image, self.ref_image_ls, self.mask = [], [], [], []
        self.n_cols, self.n_rows = 0, 0
        self.pixel_fraction_accuracy = 50
        self.subset_spacing = 20
        self.var_image = IntVar(0)
        self.var_strain = IntVar(0)
        self.dic_autoreload = IntVar(0)

        # initialized default GUI values
        self.subset_size = 50
        self.frequency = 2
        self.project_name = 'My project'
        self.description = ''
        self.master.title('1D-RTCorr tool ' + str(self.version) + ' [' + self.project_name + ']')

        # TOP MENU
        # first pull-down menu
        self.menu_bar = Menu(master)
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Exit', command=self.exit)
        self.menu_bar.add_cascade(label='File', menu=self.file_menu)

        # third pull-down menu
        self.help_menu = Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label='About')
        self.menu_bar.add_cascade(label='Help', menu=self.help_menu)

        # show the menu!!
        master.config(menu=self.menu_bar)

        # FRAMES
        # frames setup
        self.first_frameA = Frame(master)
        self.first_frameA.grid(column=0, row=0, rowspan=8)
        self.first_frameB = Frame(master)
        self.first_frameB.grid(column=1, row=0)
        self.second_frame = Frame(master)
        self.second_frame.grid(column=1, row=1)
        self.third_frame = Frame(master)
        self.third_frame.grid(column=1, row=2)
        self.fourth_frame = Frame(master)
        self.fourth_frame.grid(column=1, row=3)
        self.fifth_frame = Frame(master)
        self.fifth_frame.grid(column=1, row=4)
        self.sixth_frame = Frame(master)
        self.sixth_frame.grid(column=1, row=5)
        self.seventh_frame = Frame(master)
        self.seventh_frame.grid(column=1, row=6)

        # first_frame content
        self.img_width_dic = int(self.cam_width / self.ratio_width_dic)
        self.img_height_dic = int(self.cam_height / self.ratio_height_dic)
        self.img_width_plot = int(self.cam_width / self.ratio_width_plot)
        self.img_height_plot = int(self.cam_height / self.ratio_height_plot)

        # canvases
        self.canvas_1 = Canvas(self.first_frameA, width=2590 / 2.5, height=2048 / 2.1)
        self.canvas_1.grid(column=0, row=0)
        self.canvas_2 = Canvas(self.first_frameB, width=2590 / 4.5, height=2048 / 4)
        self.canvas_2.grid(column=0, row=0, padx=30)

        no_image_img = Image.open('graphic/no-image.png')
        no_plot_img = Image.open('graphic/no-image-plot.png')

        self.canvas_1.image = ImageTk.PhotoImage(no_image_img.resize((self.img_width_dic, self.img_height_dic), Image.ANTIALIAS))
        self.canvas_1.create_image(0, 0, image=self.canvas_1.image, anchor='nw')

        self.canvas_2.image = ImageTk.PhotoImage(no_plot_img.resize((self.img_width_plot, self.img_height_plot), Image.ANTIALIAS))
        self.canvas_2.create_image(0, 0, image=self.canvas_2.image, anchor='nw')

        # second_frame content - buttons and control
        self.initiate_camera_button = Button(self.second_frame,
                                             text='Initialize camera',
                                             width=18,
                                             command=self.camera_init)
        self.initiate_camera_button.grid(column=0, row=0, sticky=E, padx=2, pady=2)

        self.refresh_DIC_button = Button(self.second_frame,
                                         text='Reload camera image',
                                         width=18,
                                         command=self.reload_dic)
        self.refresh_DIC_button.config(state='disabled')
        self.refresh_DIC_button.grid(column=1, row=0, sticky=E, padx=2, pady=2)

        self.place_extensometers_button = Button(self.second_frame,
                                                 text='Place extensometers',
                                                 width=18,
                                                 command=self.set_extensometers_button)
        self.place_extensometers_button.config(state='disabled')
        self.place_extensometers_button.grid(column=2, row=0, sticky=W, padx=2, pady=2)

        self.px_distance_button = Button(self.second_frame,
                                         text='Get scale',
                                         width=18,
                                         command=self.get_scale)
        self.px_distance_button.config(state='disabled')
        self.px_distance_button.grid(column=1, row=1, sticky=E, padx=2, pady=2)

        self.delete_extensometers_button = Button(self.second_frame,
                                                  text='Delete extensometers',
                                                  width=18,
                                                  command=self.delete_extensometers)
        self.delete_extensometers_button.config(state='disabled')
        self.delete_extensometers_button.grid(column=2, row=1, sticky=E, padx=2, pady=2)

        # third frame content
        self.subpixel_accuracy_label = Label(self.third_frame, text='Subpixel accuracy:')
        self.subpixel_accuracy_label.grid(column=0, row=1, sticky=E, padx=2, pady=2)
        self.subpixel_accuracy_entry_var = StringVar()
        self.subpixel_accuracy_entry_var.set('%.1f' % self.pixel_fraction_accuracy)
        self.subpixel_accuracy_entry = Entry(self.third_frame, width=6, textvariable=self.subpixel_accuracy_entry_var)
        self.subpixel_accuracy_entry.bind('<Return>', (lambda _: self.callback_subpixel_fraction_accuracy_entry_var()))
        self.subpixel_accuracy_entry.grid(column=1, row=1, sticky=E, padx=2, pady=2)
        self.subpixel_accuracy_entry_label = Label(self.third_frame, text='px')
        self.subpixel_accuracy_entry_label.grid(column=2, row=1, sticky=W, padx=2, pady=2)

        self.frequency_label = Label(self.third_frame, text='Sampling rate:')
        self.frequency_label.grid(column=0, row=2, sticky=E, padx=2, pady=2)
        self.frequency_entry_var = StringVar()
        self.frequency_entry_var.set('%.3f' % self.frequency)
        self.frequency_entry = Entry(self.third_frame, width=6, textvariable=self.frequency_entry_var)
        self.frequency_entry.bind('<Return>', (lambda _: self.callback_frequency_entry_var()))
        self.frequency_entry.grid(column=1, row=2, sticky=E, padx=2, pady=2)
        self.frequency_units_label = Label(self.third_frame, text='Hz')
        self.frequency_units_label.grid(column=2, row=2, sticky=W, padx=2, pady=2)

        self.subset_size_label = Label(self.third_frame, text='Subset size:')
        self.subset_size_label.grid(column=3, row=2, sticky=E, padx=2, pady=2)
        self.subset_size_entry_var = StringVar()
        self.subset_size_entry_var.set('%.1f' % self.subset_size)
        self.subset_size_entry = Entry(self.third_frame, width=6, textvariable=self.subset_size_entry_var)
        self.subset_size_entry.bind('<Return>', (lambda _: self.callback_subset_size_entry_var()))
        self.subset_size_entry.grid(column=4, row=2, sticky=E, padx=2, pady=2)
        self.subset_size_units_label = Label(self.third_frame, text='px')
        self.subset_size_units_label.grid(column=5, row=2, sticky=W, padx=2, pady=2)

        self.scale_label = Label(self.third_frame, text='Scale:')
        self.scale_label.grid(column=0, row=3, sticky=E, padx=2, pady=2)

        self.scale_label_var = Label(self.third_frame, text='1.0')
        self.scale_label_var.grid(column=1, row=3, sticky=E, padx=2, pady=2)

        self.scale_label_units = Label(self.third_frame, text='px/mm')
        self.scale_label_units.grid(column=2, row=3, sticky=E, padx=2, pady=2)

        self.image_check = Checkbutton(self.third_frame, text="Save image files", variable=self.var_image)
        self.image_check.grid(column=6, row=1, sticky=W, padx=2, pady=2)

        self.large_strain_check = Checkbutton(self.third_frame, text="Large strain analysis", variable=self.var_strain)
        self.large_strain_check.grid(column=6, row=2, sticky=W, padx=2, pady=2)

        # fourth frame content
        self.extensometer_label = Label(self.fourth_frame, text='Extensometers', font='Helvetica 12 bold')
        self.extensometer_label.grid(column=0, row=0, columnspan=6)

        self.point_a_label = Label(self.fourth_frame, text='a', font='Helvetica 10 bold')
        self.point_a_label.grid(column=1, row=1, sticky=N, padx=2, pady=2)
        self.point_b_label = Label(self.fourth_frame, text='b', font='Helvetica 10 bold')
        self.point_b_label.grid(column=3, row=1, sticky=N, padx=2, pady=2)

        self.position_x_label = Label(self.fourth_frame, text='Position X:')
        self.position_x_label.grid(column=0, row=2, sticky=W, padx=2, pady=2)
        self.position_y_label = Label(self.fourth_frame, text='Position Y:')
        self.position_y_label.grid(column=0, row=3, sticky=W, padx=2, pady=2)

        self.position_x_entry = Entry(self.fourth_frame, width=7)
        self.position_x_entry.bind('<Return>', (lambda _: self.callback_position_x_entry()))
        self.position_x_entry.grid(column=1, row=2, sticky=W, padx=2, pady=2)

        self.position_xb_entry = Entry(self.fourth_frame, width=7)
        self.position_xb_entry.bind('<Return>', (lambda _: self.callback_position_xb_entry()))
        self.position_xb_entry.grid(column=3, row=2, sticky=W, padx=2, pady=2)

        self.position_y_entry = Entry(self.fourth_frame, width=7)
        self.position_y_entry.bind('<Return>', (lambda _: self.callback_position_y_entry()))
        self.position_y_entry.grid(column=1, row=3, sticky=W, padx=2, pady=2)

        self.position_yb_entry = Entry(self.fourth_frame, width=7)
        self.position_yb_entry.bind('<Return>', (lambda _: self.callback_position_yb_entry()))
        self.position_yb_entry.grid(column=3, row=3, sticky=W, padx=2, pady=2)

        self.position_x_units_label = Label(self.fourth_frame, text='px')
        self.position_x_units_label.grid(column=4, row=2, sticky=E)
        self.position_y_units_label = Label(self.fourth_frame, text='px')
        self.position_y_units_label.grid(column=4, row=3, sticky=E)

        self.virtual_extensometers_listbox = Listbox(self.fourth_frame, width=6, height=5)
        self.virtual_extensometers_listbox.bind('<<ListboxSelect>>', self.update_extensometer)
        self.virtual_extensometers_listbox.grid(column=5, row=1, rowspan=4, sticky=NW)

        # fifth_frame
        self.project_name_label = Label(self.fifth_frame, text='Project name:')
        self.project_name_label.grid(column=0, row=0, columnspan=2, sticky=E, padx=2, pady=2)
        self.project_name_entry_var = StringVar()
        self.project_name_entry_var.set(self.project_name)
        self.project_name_entry = Entry(self.fifth_frame, width=10, textvariable=self.project_name_entry_var)
        self.project_name_entry.bind('<Return>', (lambda _: self.callback_project_name_entry_var()))
        self.project_name_entry.grid(column=2, row=0, sticky=W, padx=2, pady=2)

        self.ari14 = font.Font(family='Arial', size=25, weight='bold')
        self.run_stop_toggle = Button(self.fifth_frame, text='START', bg='green', fg='white',
                                      command=self.run_stop_toggle, font=self.ari14)
        self.run_stop_toggle.grid(column=0, columnspan=3, row=1, pady=10)
        self.run_stop_toggle.config(state='disabled', bg='gray')

        # sixth frame
        self.label_status = Label(self.sixth_frame, text='Messages', anchor=W)
        self.label_status.grid(column=0, row=0, sticky='W', pady=2)

        # seventh frame
        self.scrollbar_output = Scrollbar(self.seventh_frame)
        self.text_status = Text(self.seventh_frame, height=5, font=("Helvetica", 9),
                                yscrollcommand=self.scrollbar_output.set, width=80)
        self.scrollbar_output.config(command=self.text_status.yview)
        self.scrollbar_output.pack(side=RIGHT, fill=Y)
        self.text_status.pack(side=LEFT, fill=X, expand=True)

    def camera_init(self):
        # camera initialization
        self.write_output('Pylon version: %s' % (pypylon.pylon_version.version))
        available_cameras = pypylon.factory.find_devices()
        self.write_output('Available_cameras: %s' % (available_cameras))

        if len(available_cameras) != 0:
            self.cam = pypylon.factory.create_device(available_cameras[self.def_cam_dic])
            self.write_output('Chosen camera: %s' % (self.cam))
            self.cam.open()
            if self.cam.opened:
                self.write_output('Camera chip temperature is: %s' % (self.cam.properties['DeviceTemperature']))
                self.write_output('Camera state: opened')
        else:
            sys.exit('No cameras available.')

        # camera settings
        self.cam.properties['ExposureAuto'] = 'Off'
        self.cam.properties['ExposureTime'] = exposure_time
        time.sleep(1)
        # GUI control settings
        self.refresh_DIC_button.config(state='normal')
        self.initiate_camera_button.config(state='disable')

        # reload camera
        for i in range(4):
            self.reload_dic()
            time.sleep(0.2)

    def run_stop_toggle(self):
        if self.run_stop_toggle.config('text')[-1] == ' STOP ':
            self.run_stop_toggle.config(text=' START ', bg='green')
            self.write_output('DIC terminated.')
            self.dic_started = False
        else:
            self.time = [0]
            self.reload_dic()
            n_ext = len(self.x_extensions)
            self.tot_extensions, self.x_extensions, self.y_extensions, self.saved_dx, self.saved_dy = [], [], [], [], []
            for i in range(n_ext):
                self.x_extensions.append([0])
                self.y_extensions.append([0])
                self.tot_extensions.append([0])
                self.saved_dx.append([0.0, 0.0])
                self.saved_dy.append([0.0, 0.0])
            self.dic_started = True
            self.run_stop_toggle.config(text=' STOP ', bg='red')
            self.write_output('DIC started.')
            self.master.update()

            # create output folder
            temp_dir = os.getcwd()
            os.chdir('output')
            time_str = time.strftime('-%Y_%m_%d-%H_%M_%S')
            new_folder_name = self.project_name + time_str
            os.makedirs(new_folder_name, 0o777)
            os.chdir(temp_dir)
            project_path = 'output/' + new_folder_name + '/'
            if self.var_strain.get() == 1:
                f_out = open(project_path + '_results_' + self.project_name + '_LSA.txt', 'w')
            else:
                f_out = open(project_path + '_results_' + self.project_name + '.txt', 'w')
            f_out.write('time [s]\tlag [s]')
            for i in range(len(self.extensometer_possitions)):
                f_out.write('\tdx_%d [mm]\tdy_%d [mm]\tdisp_P1(x)_%d [mm]\tdisp_P1(y)_%d [mm]\tdisp_P2(x)_%d [mm]\tdisp_P2(y)_%d [mm]' %
                            (i + 1, i + 1, i + 1, i + 1, i + 1, i + 1))
            f_out.write('\n')
            f_out.close()
            n_steps = 0
            cur_time = time.time()
            start_time = time.time()
            run_time = cur_time

            self.extensometer_lenghts = np.zeros((len(self.extensometer_possitions), 1))
            self.extensometer_lenghts_new = np.zeros((len(self.extensometer_possitions), 1))
            self.difference_lengths = np.zeros((len(self.extensometer_possitions), 1))

            for n in range(len(self.extensometer_possitions)):
                x = [self.extensometer_possitions[n][0][0], self.extensometer_possitions[n][0][1]]
                y = [self.extensometer_possitions[n][1][0], self.extensometer_possitions[n][1][1]]
                self.extensometer_lenghts[n] = np.sqrt(np.power(x[1] - x[0], 2) + np.power(y[1] - y[0], 2))

            while self.dic_started:
                while run_time > cur_time:
                    cur_time = time.time()
                run_time = cur_time + (1 / self.frequency)
                self.master.update()
                for image in self.cam.grab_images(1):
                    if self.var_strain.get() == 1:
                        if len(self.cur_image) == 0:
                            self.ref_image_ls = copy.deepcopy(self.ref_image)
                        else:
                            self.ref_image_ls = copy.deepcopy(self.cur_image)
                    self.cur_image = copy.deepcopy(image)

                if self.var_image.get() == 1:
                    output_image = self.project_name + '_%05.d.png' % n_steps
                    plt.imsave(arr=self.cur_image, fname=project_path + output_image, cmap=cm.gray)
                self.correlate()

                # update canvas
                self.plot_on_canvas(self.cur_image)
                self.plot_extensometers_with_displacements()

                self.time.append(round(cur_time - start_time, 3))
                lag = self.time[-1] - (n_steps * (1 / self.frequency))
                if self.var_strain.get() == 1:
                    f_out = open(project_path + '_results_' + self.project_name + '_LSA.txt', 'a')
                else:
                    f_out = open(project_path + '_results_' + self.project_name + '.txt', 'a')
                f_out.write('%.3f\t%.3f' % (self.time[-1], lag))
                for i in range(len(self.extensometer_possitions)):
                    f_out.write('\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f' % (self.x_extensions[i][-1], self.y_extensions[i][-1],
                                                                          self.saved_dx[i][0] / self.scale,
                                                                          self.saved_dy[i][0] / self.scale,
                                                                          self.saved_dx[i][1] / self.scale,
                                                                          self.saved_dy[i][1] / self.scale))
                f_out.write('\n')
                f_out.close()
                n_steps += 1
                self.show_plot()

    def exit(self):
        sys.exit('The process was terminated by user.')

    def change_camera_1(self, val):
        self.def_cam_dic = val
        print('Selected DIC cam: ' + str(val))

    def reload_dic(self):
        for image in self.cam.grab_images(1):
            self.ref_image = copy.deepcopy(image)
            self.n_rows = len(image)
            self.n_cols = len(image[0])
            self.plot_on_canvas(self.ref_image)
            self.px_distance_button.config(state='normal')
            self.place_extensometers_button.config(state='normal')
            if len(self.extensometer_possitions) > 0:
                self.plot_extensometers()

    def get_scale(self):
        for image in self.cam.grab_images(1):
            image_grayscale = np.asarray(Image.fromarray(image))

            fig = plt.figure()
            plt.imshow(image_grayscale, cmap='gray')

            [p1, p2] = plt.ginput(2)
            x = np.round([p1[0], p2[0]])
            y = np.round([p1[1], p2[1]])
            lenght = np.sqrt((x[0] - x[1]) ** 2 + (y[0] - y[1]) ** 2)
            def_lenght = simpledialog.askfloat('Scaling', 'Define reference lenght: [mm]')
            self.scale = (lenght / def_lenght)
            plt.close(fig)
            self.scale_label_var.config(text='%.2f' % self.scale)

    def set_extensometers_button(self):
        for image in self.cam.grab_images(1):
            self.ref_image = image
            image_grayscale = np.asarray(Image.fromarray(image))
            fig = plt.figure()
            plt.imshow(image_grayscale, cmap='gray')
            [p1, p2] = plt.ginput(2)
            self.x = np.round([p1[0], p2[0]])
            self.y = np.round([p1[1], p2[1]])
            plt.close(fig)
        self.add_extensometers()

    def plot_on_canvas(self, image):
        cam_1_img = Image.fromarray(image)
        # self.img_height = self.cam_height / 4
        self.h_percent_w = self.img_width_dic / cam_1_img.size[0]
        self.h_percent_h = self.img_height_dic / cam_1_img.size[1]

        img_width = int(self.h_percent_h * cam_1_img.size[0])
        self.canvas_1.image = ImageTk.PhotoImage(cam_1_img.resize((img_width, int(self.img_height_dic)), Image.ANTIALIAS))
        self.canvas_1.create_image(0, 0, image=self.canvas_1.image, anchor='nw')

    def add_extensometers(self):
        self.actual_extensometer += 1
        self.extensometer_possitions.append([self.x, self.y])
        self.x_extensions.append([0])
        self.y_extensions.append([0])
        self.tot_extensions.append([0])
        self.saved_dx.append([0.0, 0.0])
        self.saved_dy.append([0.0, 0.0])

        self.virtual_extensometers_listbox.select_clear(0, END)
        self.virtual_extensometers_listbox.delete(0, END)
        for idx, extensometer in enumerate(self.extensometer_possitions):
            self.virtual_extensometers_listbox.insert(END, idx + 1)
        self.virtual_extensometers_listbox.selection_set(self.actual_extensometer)
        self.plot_on_canvas(self.ref_image)
        self.plot_extensometers()
        self.delete_extensometers_button.config(state='normal')
        self.run_stop_toggle.config(state='normal', bg='green')

    def delete_extensometers(self):
        del self.extensometer_possitions[self.actual_extensometer]
        del self.x_extensions[self.actual_extensometer]
        del self.y_extensions[self.actual_extensometer]
        del self.tot_extensions[self.actual_extensometer]
        del self.saved_dx[self.actual_extensometer]
        del self.saved_dy[self.actual_extensometer]
        self.actual_extensometer -= 1
        self.plot_on_canvas(self.ref_image)
        self.virtual_extensometers_listbox.select_clear(0, END)
        self.virtual_extensometers_listbox.delete(0, END)
        if len(self.extensometer_possitions) == 0:
            self.delete_extensometers_button.config(state='disable')
            self.run_stop_toggle.config(state='disable')
        else:
            for idx, extensometer in enumerate(self.extensometer_possitions):
                self.virtual_extensometers_listbox.insert(END, idx + 1)
            self.virtual_extensometers_listbox.selection_set(self.actual_extensometer)
            self.plot_extensometers()

    def plot_extensometers(self):
        for i in range(len(self.extensometer_possitions)):
            x_scaled = self.extensometer_possitions[i][0] * self.h_percent_w
            y_scaled = self.extensometer_possitions[i][1] * self.h_percent_h
            if i == self.actual_extensometer:
                self.line_1 = self.canvas_1.create_line(int(x_scaled[0] - self.img_height_dic / 50), int(y_scaled[0]),
                                                        int(x_scaled[0] + self.img_height_dic / 50), int(y_scaled[0]),
                                                        fill='red', width=2)
                self.line_2 = self.canvas_1.create_line(int(x_scaled[1] - self.img_height_dic / 50), int(y_scaled[1]),
                                                        int(x_scaled[1] + self.img_height_dic / 50), int(y_scaled[1]),
                                                        fill='red', width=2)
                self.line_3 = self.canvas_1.create_line(int(x_scaled[0]), int(y_scaled[0] - self.img_height_dic / 50),
                                                        int(x_scaled[0]), int(y_scaled[0] + self.img_height_dic / 50),
                                                        fill='red', width=2)
                self.line_4 = self.canvas_1.create_line(int(x_scaled[1]), int(y_scaled[1] - self.img_height_dic / 50),
                                                        int(x_scaled[1]), int(y_scaled[1] + self.img_height_dic / 50),
                                                        fill='red', width=2)
                self.text_1 = self.canvas_1.create_text(x_scaled[0] + 20, y_scaled[0] - 20, text=str(i + 1) + 'a',
                                                        fill='red', font=13)
                self.text_2 = self.canvas_1.create_text(x_scaled[1] + 20, y_scaled[1] - 20, text=str(i + 1) + 'b',
                                                        fill='red', font=13)

                subset_size = int(float(self.subset_size_entry_var.get())) * self.h_percent_h

                self.rect = self.canvas_1.create_rectangle(int(x_scaled[0]) - subset_size / 2, int(y_scaled[0]) -
                                                           subset_size / 2, int(x_scaled[0]) + subset_size / 2, int(y_scaled[0]) +
                                                           subset_size / 2, outline='red')
                self.rect_2 = self.canvas_1.create_rectangle(int(x_scaled[1]) - subset_size / 2, int(y_scaled[1]) -
                                                             subset_size / 2, int(x_scaled[1]) + subset_size / 2, int(y_scaled[1]) +
                                                             subset_size / 2, outline='red')
            else:
                self.line_1 = self.canvas_1.create_line(int(x_scaled[0] - self.img_height_dic / 50), int(y_scaled[0]),
                                                        int(x_scaled[0] + self.img_height_dic / 50), int(y_scaled[0]),
                                                        fill='blue', width=1)
                self.line_2 = self.canvas_1.create_line(int(x_scaled[1] - self.img_height_dic / 50), int(y_scaled[1]),
                                                        int(x_scaled[1] + self.img_height_dic / 50), int(y_scaled[1]),
                                                        fill='blue', width=1)
                self.line_3 = self.canvas_1.create_line(int(x_scaled[0]), int(y_scaled[0] - self.img_height_dic / 50),
                                                        int(x_scaled[0]), int(y_scaled[0] + self.img_height_dic / 50),
                                                        fill='blue', width=1)
                self.line_4 = self.canvas_1.create_line(int(x_scaled[1]), int(y_scaled[1] - self.img_height_dic / 50),
                                                        int(x_scaled[1]), int(y_scaled[1] + self.img_height_dic / 50),
                                                        fill='blue', width=1)
                self.text_1 = self.canvas_1.create_text(x_scaled[0] + 20, y_scaled[0] - 20, text=str(i + 1) + 'a',
                                                        fill='blue', font=11)
                self.text_2 = self.canvas_1.create_text(x_scaled[1] + 20, y_scaled[1] - 20, text=str(i + 1) + 'b',
                                                        fill='blue', font=11)

        self.position_x_entry.delete(0, END)
        self.position_xb_entry.delete(0, END)
        self.position_x_entry.insert(0, str(self.extensometer_possitions[self.actual_extensometer][0][0]))
        self.position_xb_entry.insert(0, str(self.extensometer_possitions[self.actual_extensometer][0][1]))
        self.position_y_entry.delete(0, END)
        self.position_yb_entry.delete(0, END)
        self.position_y_entry.insert(0, str(self.extensometer_possitions[self.actual_extensometer][1][0]))
        self.position_yb_entry.insert(0, str(self.extensometer_possitions[self.actual_extensometer][1][1]))
        self.point_a_label.config(text='%da' % (self.actual_extensometer + 1))
        self.point_b_label.config(text='%db' % (self.actual_extensometer + 1))

    def plot_extensometers_with_displacements(self):
        for i in range(len(self.extensometer_possitions)):
            x_scaled = [0.0, 0.0]
            y_scaled = [0.0, 0.0]
            x_scaled[0] = (self.extensometer_possitions[i][0][0] + self.saved_dx[i][0]) * self.h_percent_w
            x_scaled[1] = (self.extensometer_possitions[i][0][1] + self.saved_dx[i][1]) * self.h_percent_w
            y_scaled[0] = (self.extensometer_possitions[i][1][0] + self.saved_dy[i][0]) * self.h_percent_h
            y_scaled[1] = (self.extensometer_possitions[i][1][1] + self.saved_dy[i][1]) * self.h_percent_h
            if i == self.actual_extensometer:
                self.line_1 = self.canvas_1.create_line(int(x_scaled[0] - self.img_height_dic / 50), int(y_scaled[0]),
                                                        int(x_scaled[0] + self.img_height_dic / 50), int(y_scaled[0]),
                                                        fill='red', width=2)
                self.line_2 = self.canvas_1.create_line(int(x_scaled[1] - self.img_height_dic / 50), int(y_scaled[1]),
                                                        int(x_scaled[1] + self.img_height_dic / 50), int(y_scaled[1]),
                                                        fill='red', width=2)
                self.line_3 = self.canvas_1.create_line(int(x_scaled[0]), int(y_scaled[0] - self.img_height_dic / 50),
                                                        int(x_scaled[0]), int(y_scaled[0] + self.img_height_dic / 50),
                                                        fill='red', width=2)
                self.line_4 = self.canvas_1.create_line(int(x_scaled[1]), int(y_scaled[1] - self.img_height_dic / 50),
                                                        int(x_scaled[1]), int(y_scaled[1] + self.img_height_dic / 50),
                                                        fill='red', width=2)
                self.text_1 = self.canvas_1.create_text(x_scaled[0] + 20, y_scaled[0] - 20, text=str(i + 1) + 'a',
                                                        fill='red', font=13)
                self.text_2 = self.canvas_1.create_text(x_scaled[1] + 20, y_scaled[1] - 20, text=str(i + 1) + 'b',
                                                        fill='red', font=13)

                subset_size = int(float(self.subset_size_entry_var.get())) * self.h_percent_h

                self.rect = self.canvas_1.create_rectangle(int(x_scaled[0]) - subset_size / 2, int(y_scaled[0]) -
                                                           subset_size / 2, int(x_scaled[0]) + subset_size / 2, int(y_scaled[0]) +
                                                           subset_size / 2, outline='red')
                self.rect_2 = self.canvas_1.create_rectangle(int(x_scaled[1]) - subset_size / 2, int(y_scaled[1]) -
                                                             subset_size / 2, int(x_scaled[1]) + subset_size / 2, int(y_scaled[1]) +
                                                             subset_size / 2, outline='red')
            else:
                self.line_1 = self.canvas_1.create_line(int(x_scaled[0] - self.img_height_dic / 50), int(y_scaled[0]),
                                                        int(x_scaled[0] + self.img_height_dic / 50), int(y_scaled[0]),
                                                        fill='blue', width=1)
                self.line_2 = self.canvas_1.create_line(int(x_scaled[1] - self.img_height_dic / 50), int(y_scaled[1]),
                                                        int(x_scaled[1] + self.img_height_dic / 50), int(y_scaled[1]),
                                                        fill='blue', width=1)
                self.line_3 = self.canvas_1.create_line(int(x_scaled[0]), int(y_scaled[0] - self.img_height_dic / 50),
                                                        int(x_scaled[0]), int(y_scaled[0] + self.img_height_dic / 50),
                                                        fill='blue', width=1)
                self.line_4 = self.canvas_1.create_line(int(x_scaled[1]), int(y_scaled[1] - self.img_height_dic / 50),
                                                        int(x_scaled[1]), int(y_scaled[1] + self.img_height_dic / 50),
                                                        fill='blue', width=1)
                self.text_1 = self.canvas_1.create_text(x_scaled[0] + 20, y_scaled[0] - 20, text=str(i + 1) + 'a',
                                                        fill='blue', font=11)
                self.text_2 = self.canvas_1.create_text(x_scaled[1] + 20, y_scaled[1] - 20, text=str(i + 1) + 'b',
                                                        fill='blue', font=11)

        self.position_x_entry.delete(0, END)
        self.position_xb_entry.delete(0, END)
        self.position_x_entry.insert(0, str(self.extensometer_possitions[self.actual_extensometer][0][0]))
        self.position_xb_entry.insert(0, str(self.extensometer_possitions[self.actual_extensometer][0][1]))
        self.position_y_entry.delete(0, END)
        self.position_yb_entry.delete(0, END)
        self.position_y_entry.insert(0, str(self.extensometer_possitions[self.actual_extensometer][1][1]))
        self.position_yb_entry.insert(0, str(self.extensometer_possitions[self.actual_extensometer][1][0]))
        self.point_a_label.config(text='%da' % (self.actual_extensometer + 1))
        self.point_b_label.config(text='%db' % (self.actual_extensometer + 1))

    def update_extensometer(self, event):
        try:
            widget = event.widget
            selection = widget.curselection()
            value = widget.get(selection[0])
        except IndexError:
            pass
        try:
            self.actual_extensometer = value * 1 - 1
        except UnboundLocalError:
            self.actual_extensometer = 0
        self.plot_on_canvas(self.ref_image)
        self.plot_extensometers()
        self.point_a_label.config(text='%da' % (self.actual_extensometer + 1))
        self.point_b_label.config(text='%db' % (self.actual_extensometer + 1))
        self.show_plot()

    def callback_frequency_entry_var(self):
        self.frequency = float(self.frequency_entry_var.get())
        self.write_output('Sampling rate was set to: %.3f Hz.' % (self.frequency))

    def callback_subset_size_entry_var(self):
        self.subset_size = float(self.subset_size_entry_var.get())
        self.write_output('Subset size was set to: %d px.' % (self.subset_size))
        self.plot_on_canvas(self.ref_image)
        self.plot_extensometers()

    def callback_subpixel_fraction_accuracy_entry_var(self):
        self.pixel_fraction_accuracy = float(self.subpixel_accuracy_entry_var.get())
        self.write_output('Pixel fraction accuracy was set to: %d px.' % (self.pixel_fraction_accuracy))

    def callback_project_name_entry_var(self):
        self.project_name = self.project_name_entry_var.get()
        self.master.title('1D-RTCorr tool ' + str(self.version) + ' [' + self.project_name_entry_var.get() + ']')

    def callback_position_x_entry(self):
        pos_1, pos_2 = 0, 0
        val = float(self.position_x_entry.get())
        if val > self.n_cols * self.scale:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = self.n_cols * self.scale
        elif val < 0:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = 0
        else:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = val * 1
        self.write_output('Extensometer %da position x set to: %.2f mm.' % (self.actual_extensometer + 1,
                                                                            self.extensometer_possitions[self.actual_extensometer][pos_1]
                                                                            [pos_2]))
        self.plot_on_canvas(self.ref_image)
        self.plot_extensometers()

    def callback_position_xb_entry(self):
        pos_1, pos_2 = 0, 1
        val = float(self.position_xb_entry.get())
        if val > self.n_cols * self.scale:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = self.n_cols * self.scale
        elif val < 0:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = 0
        else:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = val * 1
        self.write_output('Extensometer %db position x set to: %.2f mm.' % (self.actual_extensometer + 1,
                                                                            self.extensometer_possitions[self.actual_extensometer][pos_1]
                                                                            [pos_2]))
        self.plot_on_canvas(self.ref_image)
        self.plot_extensometers()

    def callback_position_y_entry(self):
        pos_1, pos_2 = 1, 0
        val = float(self.position_y_entry.get())
        if val > self.n_rows * self.scale:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = self.n_rows * self.scale
        elif val < 0:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = 0
        else:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = val * 1
        self.write_output('Extensometer %da position y set to: %.2f mm.' % (self.actual_extensometer + 1,
                                                                            self.extensometer_possitions[self.actual_extensometer][pos_1]
                                                                            [pos_2]))
        self.plot_on_canvas(self.ref_image)
        self.plot_extensometers()

    def callback_position_yb_entry(self):
        pos_1, pos_2 = 1, 1
        val = float(self.position_yb_entry.get())
        if val > self.n_rows * self.scale:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = self.n_rows * self.scale
        elif val < 0:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = 0
        else:
            self.extensometer_possitions[self.actual_extensometer][pos_1][pos_2] = val * 1
        self.write_output('Extensometer %db position y set to: %.2f mm.' % (self.actual_extensometer + 1,
                                                                            self.extensometer_possitions[self.actual_extensometer][pos_1]
                                                                            [pos_2]))
        self.plot_on_canvas(self.ref_image)
        self.plot_extensometers()

    def write_output(self, string_to_display):
        self.text_status.insert(INSERT, string_to_display + '\n')
        self.text_status.mark_set('insert', END)
        self.text_status.see('insert')

    def correlate(self):
        dx, dy = [0, 0], [0, 0]
        for n in range(len(self.extensometer_possitions)):
            x = [self.extensometer_possitions[n][0][0], self.extensometer_possitions[n][0][1]]
            y = [self.extensometer_possitions[n][1][0], self.extensometer_possitions[n][1][1]]

            # search region boundaries
            for i in range(2):
                min_xr = int(max(1, x[i] - np.round(self.subset_size / 2)))
                max_xr = int(min(x[i] + np.round(self.subset_size / 2), self.n_cols))
                min_yr = int(max(1, y[i] - np.round(self.subset_size / 2)))
                max_yr = int(min(y[i] + np.round(self.subset_size / 2), self.n_rows))

                # create search regions
                if self.var_strain.get() == 1:
                    search_region_ref = self.ref_image_ls[min_yr: max_yr, min_xr: max_xr]
                else:
                    search_region_ref = self.ref_image[min_yr: max_yr, min_xr: max_xr]
                search_region_cur = self.cur_image[min_yr: max_yr, min_xr: max_xr]

                # calculate displacements
                [x_displacement, y_displacement] = image_registration.register_images(search_region_ref, search_region_cur,
                                                                                      self.pixel_fraction_accuracy)
                if self.var_strain.get() == 1:
                    dx[i] = (x_displacement + self.saved_dx[n][i]) / self.scale
                    dy[i] = (y_displacement + self.saved_dy[n][i]) / self.scale
                else:
                    dx[i] = x_displacement / self.scale
                    dy[i] = y_displacement / self.scale

            self.extensometer_lenghts_new[n] = np.sqrt(np.power(x[1] + dx[1] - x[0] - dx[0], 2) + np.power(y[1] + dx[1] - y[0] - dy[0], 2))
            self.difference_lengths[n] = self.extensometer_lenghts_new[n] - self.extensometer_lenghts[n]
            self.saved_dx[n] = np.array(dx) * self.scale
            self.saved_dy[n] = np.array(dy) * self.scale
            self.x_extensions[n].append(dx[1] - dx[0])
            self.y_extensions[n].append(dy[1] - dy[0])
            self.tot_extensions[n].append(np.sign(self.difference_lengths[n]) * (np.sqrt((dx[1] - dx[0]) ** 2 + (dy[1] - dy[0]) ** 2)))

    def show_plot(self):
        canvas_width = self.canvas_2.winfo_width()
        canvas_height = self.canvas_2.winfo_height()
        self.canvas_2.delete('all')
        fig_1 = mpl.figure.Figure(figsize=(canvas_width / 100, canvas_height / 100))
        ax_1 = fig_1.add_subplot(111)
        ax_1.set_xlabel('Time [s]')
        ax_1.set_ylabel('Total extension [mm]')

        for i in range(len(self.x_extensions)):
            if i == self.actual_extensometer:
                ax_1.plot(self.time, self.tot_extensions[i], color='red', linewidth=1.5)
            else:
                ax_1.plot(self.time, self.tot_extensions[i], color='blue', linewidth=1.0)
        self.fig_photo = draw_figure(self.canvas_2, fig_1)


root = Tk()
my_gui = DICGUI(root)
root.mainloop()

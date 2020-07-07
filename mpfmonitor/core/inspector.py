import logging

# will change these to specific imports once code is more final
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

import os


class InspectorWindow(QWidget):

    def __init__(self, mpfmon):
        self.mpfmon = mpfmon
        super().__init__()
        self.ui = None

        self.log = logging.getLogger('Core')

        self.draw_ui()
        self.attach_signals()

        self.already_hidden = False
        self.added_index = 0

    def draw_ui(self):
        # Load ui file from ./ui/
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "inspector.ui")
        self.ui = uic.loadUi(ui_path, self)

        self.ui.setWindowTitle('Inspector')

        self.ui.move(self.mpfmon.local_settings.value('windows/inspector/pos',
                                                   QPoint(1100, 500)))
        self.ui.resize(self.mpfmon.local_settings.value('windows/inspector/size',
                                                     QSize(300, 300)))

    def attach_signals(self):
        self.ui.toggle_inspector_button.clicked.connect(self.toggle_inspector_mode)

        self.ui.size_slider.valueChanged.connect(self.slider_drag)  # Doesn't save value, just for live preview
        self.ui.size_slider.sliderReleased.connect(self.slider_changed)  # Saves value on release
        self.ui.size_spinbox.valueChanged.connect(self.spinbox_changed)

        self.ui.reset_to_defaults_button.clicked.connect(self.force_resize_last_device)
        self.ui.delete_last_device_button.clicked.connect(self.delete_last_device)

    def toggle_inspector_mode(self):
        inspector_enabled = not self.mpfmon.inspector_enabled
        if self.registered_inspector_cb:
            self.set_inspector_val_cb(inspector_enabled)
            if inspector_enabled:
                self.log.debug('Inspector mode toggled ON')
            else:
                self.log.debug('Inspector mode toggled OFF')
                self.clear_last_selected_device()

    def register_set_inspector_val_cb(self, cb):
        self.registered_inspector_cb = True
        self.set_inspector_val_cb = cb

    def update_last_selected(self, pf_widget=None):
        if pf_widget is not None:
            self.last_pf_widget = pf_widget
            text = '"' + str(self.last_pf_widget.name) + '" Size:'
            self.ui.device_group_box.setTitle(text)
            self.ui.size_slider.setValue(self.last_pf_widget.size * 100)
            self.ui.size_spinbox.setValue(self.last_pf_widget.size)


    def slider_drag(self):
        # For live preview
        new_size = self.ui.size_slider.value() / 100  # convert from int to float
        self.resize_last_device(new_size=new_size, save=False)

    def slider_changed(self):
        new_size = self.ui.size_slider.value() / 100  # convert from int to float
        # Update spinbox value
        self.ui.size_spinbox.setValue(new_size)

        # Don't need to call resize_last_device because updating the spinbox takes care of it
        # self.resize_last_device(new_size=new_size)

    def spinbox_changed(self):
        new_size = self.ui.size_spinbox.value()
        # Update slider value
        self.ui.size_slider.setValue(new_size*100)

        self.resize_last_device(new_size=new_size)



    def clear_last_selected_device(self):
        # Must be called AFTER spinbox valueChanged is set. Otherwise slider will not follow

        # self.last_selected_label.setText("Default Device Size:")
        self.ui.device_group_box.setTitle("Default Device:")
        self.last_pf_widget = None
        self.ui.size_spinbox.setValue(self.mpfmon.pf_device_size) # Reset the value to the stored default.


    def resize_last_device(self, new_size=None, save=True):
        new_size = round(new_size, 3)
        if self.last_pf_widget is not None:
            self.last_pf_widget.set_size(new_size)
            self.last_pf_widget.update_pos(save=save)
            self.mpfmon.view.resizeEvent()

        else:   # Change the default size.
            self.mpfmon.pf_device_size = new_size
            self.mpfmon.config["device_size"] = new_size

            if save:
                self.resize_all_devices()  # Apply new sizes to all devices without default sizes
                self.mpfmon.view.resizeEvent()  # Re draw the playfield
                self.mpfmon.save_config()  # Save the config with new default to disk


    def delete_last_device(self):
        if self.last_pf_widget is not None:
            self.last_pf_widget.destroy()
            self.clear_last_selected_device()
        else:
            self.log.info("No device selected to delete")

    def force_resize_last_device(self):
        if self.last_pf_widget is not None:

            # Redraw the device without saving
            default_size = self.mpfmon.pf_device_size
            self.resize_last_device(new_size=default_size, save=False)

            # Update the device info and clear saved size data
            self.last_pf_widget.resize_to_default(force=True)


            # Redraw the device
        else:
            self.spinbox.setValue(0.07)
            self.log.info("No device selected to resize")

    def resize_all_devices(self):
        for i in self.mpfmon.scene.items():
            try:
                i.resize_to_default()
            except AttributeError as e:
                # Can't resize object. That's ok.
                pass

    def register_last_selected_cb(self):
        self.mpfmon.inspector_window_last_selected_cb = self.update_last_selected


    def closeEvent(self, event):
        self.mpfmon.write_local_settings()
        event.accept()
        self.mpfmon.check_if_quit()

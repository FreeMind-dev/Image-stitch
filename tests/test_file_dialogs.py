from image_stitch.gui import file_dialogs


def test_open_filenames_uses_zenity_output(monkeypatch):
    monkeypatch.setattr(file_dialogs, "which", lambda name: "/usr/bin/zenity")
    monkeypatch.setattr(
        file_dialogs,
        "_run_zenity",
        lambda args: "/tmp/a.png\n/tmp/b.gif\n",
    )

    files = file_dialogs.ask_open_filenames(
        title="Select Images",
        filetypes=[("Image Files", "*.png *.gif")],
    )

    assert files == ("/tmp/a.png", "/tmp/b.gif")


def test_open_filenames_cancel_does_not_fall_back_to_tk(monkeypatch):
    monkeypatch.setattr(file_dialogs, "which", lambda name: "/usr/bin/zenity")
    monkeypatch.setattr(file_dialogs, "_run_zenity", lambda args: None)
    monkeypatch.setattr(
        file_dialogs.filedialog,
        "askopenfilenames",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("Tk fallback used")),
    )

    assert file_dialogs.ask_open_filenames(
        title="Select Images",
        filetypes=[("Image Files", "*.png")],
    ) == ()


def test_save_as_cancel_does_not_fall_back_to_tk(monkeypatch):
    monkeypatch.setattr(file_dialogs, "which", lambda name: "/usr/bin/zenity")
    monkeypatch.setattr(file_dialogs, "_run_zenity", lambda args: None)
    monkeypatch.setattr(
        file_dialogs.filedialog,
        "asksaveasfilename",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("Tk fallback used")),
    )

    assert file_dialogs.ask_save_as_filename(
        title="Save As",
        filetypes=[("PNG Files", "*.png")],
        defaultextension=".png",
    ) == ""


def test_save_as_appends_default_extension_for_zenity(monkeypatch):
    monkeypatch.setattr(file_dialogs, "which", lambda name: "/usr/bin/zenity")
    monkeypatch.setattr(file_dialogs, "_run_zenity", lambda args: "/tmp/output\n")

    path = file_dialogs.ask_save_as_filename(
        title="Save As",
        filetypes=[("PNG Files", "*.png")],
        defaultextension=".png",
    )

    assert path == "/tmp/output.png"

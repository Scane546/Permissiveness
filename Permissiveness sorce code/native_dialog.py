import ctypes
from ctypes import wintypes, POINTER, c_void_p, byref, HRESULT
from ctypes.wintypes import HWND, DWORD, LPCWSTR
import comtypes
from comtypes import GUID, COMMETHOD, IUnknown
import comtypes.client

OFN_EXPLORER = 0x00080000
OFN_FILEMUSTEXIST = 0x00001000
OFN_HIDEREADONLY = 0x00000004

class OPENFILENAME(ctypes.Structure):
    _fields_ = [
        ('lStructSize', wintypes.DWORD),
        ('hwndOwner', wintypes.HWND),
        ('hInstance', wintypes.HINSTANCE),
        ('lpstrFilter', wintypes.LPCWSTR),
        ('lpstrCustomFilter', wintypes.LPWSTR),
        ('nMaxCustFilter', wintypes.DWORD),
        ('nFilterIndex', wintypes.DWORD),
        ('lpstrFile', wintypes.LPWSTR),
        ('nMaxFile', wintypes.DWORD),
        ('lpstrFileTitle', wintypes.LPWSTR),
        ('nMaxFileTitle', wintypes.DWORD),
        ('lpstrInitialDir', wintypes.LPCWSTR),
        ('lpstrTitle', wintypes.LPCWSTR),
        ('Flags', wintypes.DWORD),
        ('nFileOffset', wintypes.WORD),
        ('nFileExtension', wintypes.WORD),
        ('lpstrDefExt', wintypes.LPCWSTR),
        ('lCustData', wintypes.LPARAM),
        ('lpfnHook', wintypes.LPVOID),
        ('lpTemplateName', wintypes.LPCWSTR),
        ('pvReserved', wintypes.LPVOID),
        ('dwReserved', wintypes.DWORD),
        ('FlagsEx', wintypes.DWORD),
    ]

def get_hwnd(parent=None):
    if parent:
        try:
            return parent.winfo_id()
        except:
            pass
    return None

def askopenfilename(title="Select File", filetypes=None, parent=None):
    try:
        buffer = ctypes.create_unicode_buffer(260)
        if filetypes:
            filter_str = ""
            for name, pattern in filetypes:
                filter_str += f"{name}\0{pattern}\0"
            filter_str += "\0"
        else:
            filter_str = "All Files\0*.*\0\0"
        ofn = OPENFILENAME()
        ofn.lStructSize = ctypes.sizeof(OPENFILENAME)
        ofn.hwndOwner = get_hwnd(parent)
        ofn.lpstrFile = ctypes.cast(buffer, wintypes.LPWSTR)
        ofn.nMaxFile = 260
        ofn.lpstrFilter = filter_str
        ofn.nFilterIndex = 1
        ofn.lpstrTitle = title
        ofn.Flags = OFN_EXPLORER | OFN_FILEMUSTEXIST | OFN_HIDEREADONLY
        if ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
            return buffer.value
        return ""
    except Exception as e:
        print(f"Error in askopenfilename: {e}")
        return ""

def askopenfilenames(title="Select Files", filetypes=None, parent=None):
    """Выбор нескольких файлов"""
    try:
        from tkinter import filedialog
        import tkinter as tk
        
        # Создаем временное скрытое окно если parent не передан
        if parent is None:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            result = filedialog.askopenfilenames(
                title=title or "Выберите файлы",
                filetypes=filetypes or [("All files", "*.*")],
                parent=root
            )
            root.destroy()
            return list(result) if result else []
        else:
            result = filedialog.askopenfilenames(
                title=title or "Выберите файлы",
                filetypes=filetypes or [("All files", "*.*")],
                parent=parent
            )
            return list(result) if result else []
        
    except Exception as e:
        print(f"Error in askopenfilenames: {e}")
        return []

# Определяем IShellItem интерфейс
class IShellItem(IUnknown):
    _iid_ = GUID('{43826D1E-E718-42EE-BC55-A1E261C37BFE}')
    _methods_ = [
        COMMETHOD([], HRESULT, 'BindToHandler'),
        COMMETHOD([], HRESULT, 'GetParent'),
        COMMETHOD([], HRESULT, 'GetDisplayName',
                  (['in'], DWORD, 'sigdnName'),
                  (['out'], POINTER(LPCWSTR), 'ppszName')),
        COMMETHOD([], HRESULT, 'GetAttributes'),
        COMMETHOD([], HRESULT, 'Compare'),
    ]

# Определяем IFileDialog интерфейс
class IFileDialog(IUnknown):
    _iid_ = GUID('{42F85136-DB7E-439C-85F1-E4075D135FC8}')
    _methods_ = [
        COMMETHOD([], HRESULT, 'Show', (['in'], HWND, 'hwndOwner')),
        COMMETHOD([], HRESULT, 'SetFileTypes'),
        COMMETHOD([], HRESULT, 'SetFileTypeIndex'),
        COMMETHOD([], HRESULT, 'GetFileTypeIndex'),
        COMMETHOD([], HRESULT, 'Advise'),
        COMMETHOD([], HRESULT, 'Unadvise'),
        COMMETHOD([], HRESULT, 'SetOptions', (['in'], DWORD, 'fos')),
        COMMETHOD([], HRESULT, 'GetOptions'),
        COMMETHOD([], HRESULT, 'SetDefaultFolder'),
        COMMETHOD([], HRESULT, 'SetFolder'),
        COMMETHOD([], HRESULT, 'GetFolder'),
        COMMETHOD([], HRESULT, 'GetCurrentSelection'),
        COMMETHOD([], HRESULT, 'SetFileName'),
        COMMETHOD([], HRESULT, 'GetFileName'),
        COMMETHOD([], HRESULT, 'SetTitle', (['in'], LPCWSTR, 'pszTitle')),
        COMMETHOD([], HRESULT, 'SetOkButtonLabel'),
        COMMETHOD([], HRESULT, 'SetFileNameLabel'),
        COMMETHOD([], HRESULT, 'GetResult', (['out'], POINTER(POINTER(IShellItem)), 'ppsi')),
        COMMETHOD([], HRESULT, 'AddPlace'),
        COMMETHOD([], HRESULT, 'SetDefaultExtension'),
        COMMETHOD([], HRESULT, 'Close'),
        COMMETHOD([], HRESULT, 'SetClientGuid'),
        COMMETHOD([], HRESULT, 'ClearClientData'),
        COMMETHOD([], HRESULT, 'SetFilter'),
    ]

def askdirectory(title="Select Folder", parent=None, initialdir=None):
    """Выбор папки через tkinter - самый надежный метод"""
    try:
        from tkinter import filedialog
        import tkinter as tk
        
        # Создаем временное скрытое окно если parent не передан
        if parent is None:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            result = filedialog.askdirectory(
                title=title or "Выберите папку",
                initialdir=initialdir,
                parent=root
            )
            root.destroy()
            return result if result else ""
        else:
            # Используем переданное родительское окно
            result = filedialog.askdirectory(
                title=title or "Выберите папку",
                initialdir=initialdir,
                parent=parent
            )
            return result if result else ""
        
    except Exception as e:
        print(f"Error in askdirectory: {e}")
        import traceback
        traceback.print_exc()
        return ""

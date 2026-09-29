"""Small, reversible UI translation layer. Config syntax and user values stay literal."""

from __future__ import annotations

import locale
import re
import html

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, GObject, Gtk


ARABIC = {
    'App Settings': 'إعدادات التطبيق', 'App menu': 'قائمة التطبيق',
    'Add rule': 'إضافة قاعدة', 'Window Rule': 'قاعدة نافذة', 'Layer Rule': 'قاعدة طبقة',
    'New Window Rule': 'قاعدة نافذة جديدة', 'New Layer Shell Rule': 'قاعدة طبقة جديدة',
    'Application ID (regex, e.g. firefox, foot)': 'معرّف التطبيق (تعبير نمطي، مثل firefox أو foot)',
    'Window Title (regex, optional)': 'عنوان النافذة (تعبير نمطي، اختياري)',
    'Layer Name (e.g. rofi, fuzzel, waybar)': 'اسم الطبقة (مثل rofi أو fuzzel أو waybar)',
    'Open Animation (e.g. zoom, slide)': 'حركة الفتح (مثل zoom أو slide)',
    'Close Animation (e.g. zoom, slide)': 'حركة الإغلاق (مثل zoom أو slide)',
    'Add Rule': 'إضافة القاعدة', 'Add Layer Rule': 'إضافة قاعدة الطبقة',
    'No arguments entered': 'لم تُدخل معاملات',
    'The documentation does not confirm the attributes for this action. Arguments remain editable.': 'لا تؤكد الوثائق خصائص هذا الإجراء. يمكنك إدخال المعاملات وتعديلها.',
    'Bindings in your configuration and sources': 'الاختصارات في ملف الإعدادات وملفات مصادره',
    'Presets': 'الإعدادات المسبقة',
    'Save Current Setup as Preset': 'حفظ الإعدادات الحالية كإعداد مسبق',
    'Preset Name': 'اسم الإعداد المسبق',
    'Saved Presets': 'الإعدادات المسبقة المحفوظة',
    'Switch to preset': 'التبديل إلى هذا الإعداد',
    'No saved presets found': 'لا توجد إعدادات مسبقة محفوظة',
    'Switching a preset updates the active config.conf and its sources.': 'يحدّث التبديل ملف config.conf النشط وملفات مصادره.',
    'Could not activate configuration': 'تعذر تفعيل الإعدادات',
    'The previous configuration is unchanged. Your edits remain available for correction.': 'لم تتغير الإعدادات السابقة. تبقى تعديلاتك متاحة للتصحيح.',
    'Previous configuration restored.': 'تمت استعادة الإعدادات السابقة.',
    'Your edits remain unsaved.': 'تبقى تعديلاتك غير محفوظة.',
    'Checking with Mango…': 'جارٍ التحقق باستخدام Mango…',
    'Files changed on disk. Your unsaved edits are kept; reload to review.': 'تغيّرت الملفات على القرص. تعديلاتك غير المحفوظة باقية؛ أعد التحميل للمراجعة.',
    'Could not read configuration files': 'تعذرت قراءة ملفات الإعدادات',
    'Save Failed': 'تعذر الحفظ',
    # Navigation and common actions
    "Studio": "الاستوديو", "Workspace": "مساحة العمل", "Interaction": "التفاعل", "System": "النظام",
    "Overview": "نظرة عامة", "Appearance": "المظهر", "Effects": "التأثيرات", "Motion": "الحركة",
    "Displays": "الشاشات", "Layouts": "التخطيطات", "Workspaces": "مساحات العمل",
    "Keyboard shortcuts": "اختصارات لوحة المفاتيح", "Input devices": "أجهزة الإدخال",
    "Mouse & gestures": "الفأرة والإيماءات", "Window rules": "قواعد النوافذ",
    "Command builder": "منشئ الأوامر", "Startup": "بدء التشغيل", "Environment": "البيئة",
    "Behavior": "السلوك", "Config editor": "محرر الإعدادات", "All settings": "كل الإعدادات",
    "Navigation": "التنقل", "Settings": "الإعدادات", "Save changes": "حفظ التغييرات",
    "Save changes •": "حفظ التغييرات •", "Review changes": "مراجعة التغييرات",
    "Undo": "تراجع", "Redo": "إعادة", "Preferences": "التفضيلات", "Profiles": "الملفات الشخصية",
    "Backups & Snapshots": "النسخ الاحتياطية واللقطات", "Keyboard Shortcuts": "اختصارات لوحة المفاتيح",
    "About MangoMod": "حول MangoMod", "Main Menu": "القائمة الرئيسية",
    "Find a section…": "ابحث عن قسم…", "No matching sections": "لا توجد أقسام مطابقة",
    "All changes saved": "كل التغييرات محفوظة",
    "Unsaved changes · review before saving": "تغييرات غير محفوظة · راجعها قبل الحفظ",
    "MANGO / WORKSPACE STUDIO": "MANGO / استوديو مساحة العمل",
    # Preferences and themes
    "MangoMod Options": "خيارات MangoMod", "Automatic Backups": "نسخ احتياطية تلقائية",
    "Create timestamped snapshot on save": "إنشاء لقطة مؤرخة عند الحفظ",
    "Backup Retention Limit": "عدد النسخ الاحتياطية المحفوظة",
    "Live Reload on Save": "إعادة التحميل عند الحفظ",
    "Trigger compositor hot-reload immediately upon saving": "إعادة تحميل مدير النوافذ فور الحفظ",
    "Validate on Save": "التحقق عند الحفظ",
    "Verify config syntax using mango -c -p before saving": "التحقق من صيغة الإعدادات قبل الحفظ",
    "Theme": "السمة", "Built-in or your own CSS": "سمة مدمجة أو ملف CSS مخصص",
    "Palette preview": "معاينة الألوان", "Niri Violet": "بنفسجي Niri", "Oasis Teal": "واحة فيروزية",
    "Mode": "الوضع", "Libadwaita light/dark/system": "فاتح أو داكن أو حسب النظام",
    "System": "النظام", "Light": "فاتح", "Dark": "داكن",
    "Language": "اللغة", "Use system language": "استخدام لغة النظام",
    "English": "الإنجليزية", "Arabic": "العربية",
    "Mango Dark": "مانجو الداكنة", "Ripe Paper (light)": "ورق مانجو الفاتح",
    "Sahara Sand (light)": "رمال الصحراء الفاتحة",
    # Command builder
    "Command Builder": "منشئ الأوامر", "Open binding": "فتح اختصار", "New": "جديد",
    "Apply to config": "تطبيق على الإعدادات", "Build a shortcut": "إنشاء اختصار",
    "Choose a trigger. Add actions. Select any block to edit its attributes.": "اختر مُحفّزًا، ثم أضف الإجراءات. اضغط أي كتلة لتعديل خصائصها.",
    "YOUR SHORTCUT": "اختصارك", "Undo draft edit": "تراجع عن تعديل المسودة",
    "Redo draft edit": "إعادة تعديل المسودة", "WHEN": "عندما",
    "Select to change input or record a shortcut": "اضغط لتغيير الإدخال أو تسجيل اختصار",
    "What should happen?": "ماذا ينبغي أن يحدث؟",
    "Add an action from the sidebar, or start with a template.": "أضف إجراءً من اللوحة الجانبية أو ابدأ بقالب.",
    "＋ Add another action": "＋ إضافة إجراء آخر", "Add action": "إضافة إجراء",
    "Attributes": "الخصائص", "Find an action…": "ابحث عن إجراء…",
    "All actions": "كل الإجراءات", "Quick-start templates": "قوالب سريعة",
    "No matching actions. Use a custom command below.": "لا توجد إجراءات مطابقة. استخدم أمرًا مخصصًا أدناه.",
    "＋ Custom command": "＋ أمر مخصص", "Custom command": "أمر مخصص",
    "ACTION ATTRIBUTES": "خصائص الإجراء", "TRIGGER ATTRIBUTES": "خصائص المُحفّز",
    "Command": "الأمر", "Arguments": "المعاملات", "Edit raw command and arguments": "تعديل الأمر والمعاملات كنص",
    "This action has no attributes to configure.": "لا توجد خصائص لهذا الإجراء.",
    "Move up": "نقل للأعلى", "Move down": "نقل للأسفل",
    "Duplicate action": "نسخ الإجراء", "Remove action": "حذف الإجراء",
    "Keyboard": "لوحة المفاتيح", "Mouse button": "زر الفأرة", "Scroll wheel": "عجلة التمرير",
    "Touchpad gesture": "إيماءة لوحة اللمس", "Lid switch": "مفتاح الغطاء",
    "● Record shortcut": "● تسجيل اختصار", "Modifiers": "المفاتيح المعدِّلة",
    "Fingers": "عدد الأصابع", "Advanced trigger options": "خيارات المُحفّز المتقدمة",
    "Key mode": "وضع المفاتيح", "Review diff": "مراجعة الفرق",
    "Config preview": "معاينة الإعدادات", "Draft only · Apply stages changes for Save": "مسودة فقط · التطبيق يجهز التغييرات للحفظ",
    "Share this keyboard shortcut": "مشاركة اختصار لوحة المفاتيح",
    "Works while locked": "يعمل أثناء القفل", "Match typed symbol": "مطابقة الرمز المكتوب",
    "On key release": "عند تحرير المفتاح", "Pass key to application": "تمرير المفتاح للتطبيق",
    "Allow shared shortcut": "السماح باختصار مشترك",
    "Choose a trigger, then add actions. Select a block to edit it.": "اختر المُحفّز ثم أضف الإجراءات. اضغط كتلة لتعديلها.",
    "Add an action": "إضافة إجراء", "Browse actions": "استعراض الإجراءات",
    "Trigger settings": "إعدادات المُحفّز", "Action settings": "إعدادات الإجراء",
    "Choose what happens when the shortcut runs.": "اختر ما يحدث عند تشغيل الاختصار.",
    "Changes update the shortcut blocks immediately.": "تظهر التغييرات فورًا في كتل الاختصار.",
    "01 · WHEN": "٠١ · عند", "02 · ADD AN ACTION": "٠٢ · أضف إجراءً",
    "Pick an action on the side, or try one of these.": "اختر إجراءً من الجانب أو جرّب أحد هذه الخيارات.",
    "Launch an app": "تشغيل تطبيق", "Move a window": "تحريك نافذة",
    "Switch workspace": "تبديل مساحة العمل",
    "Open existing binding": "فتح اختصار موجود", "Bindings in your main configuration": "الاختصارات في ملف الإعدادات الرئيسي",
    "Find a key or command…": "ابحث عن مفتاح أو أمر…",
    "No bindings yet. Start with an action or template.": "لا توجد اختصارات بعد. ابدأ بإجراء أو قالب.",
    "Record shortcut": "تسجيل اختصار", "Press your shortcut": "اضغط اختصارك",
    "Escape cancels. If your compositor intercepts it, enter the key manually.": "اضغط Escape للإلغاء. إذا اعترضه مدير النوافذ، أدخل المفتاح يدويًا.",
    "Cancel": "إلغاء", "Discard this draft?": "تجاهل هذه المسودة؟",
    "Your unapplied shortcut edits will be discarded.": "سيتم تجاهل تعديلات الاختصار غير المطبقة.",
    "Keep editing": "متابعة التعديل", "Discard draft": "تجاهل المسودة",
    # Forward-compatible options
    "All Settings": "كل الإعدادات", "Complete Mangowm settings catalog": "دليل إعدادات Mango الكامل",
    "Search all settings…": "ابحث في كل الإعدادات…",
    "Other config options": "خيارات إعدادات أخرى",
    "Options absent from this version's catalog stay intact. Edit or add one here if your Mango version supports it.": "تبقى الخيارات غير الموجودة في هذا الإصدار كما هي. يمكنك تعديلها أو إضافتها إذا كان إصدار Mango يدعمها.",
    "Option name": "اسم الخيار", "Value": "القيمة", "Add option": "إضافة خيار",
    "Custom or newer Mango option": "خيار مخصص أو أحدث من Mango", "Apply": "تطبيق",
}

ARABIC.update({
    # Theme manager and progressive builder
    "Choose a theme and its light or dark variant.": "اختر سمة ونسختها الفاتحة أو الداكنة.",
    "Built-in and created themes": "السمات المدمجة والمُنشأة",
    "Created themes have only the variants you save": "تتوفر للسمات المُنشأة النسخ التي تحفظها فقط",
    "Add a new theme or another variant": "أضف سمة جديدة أو نسخة أخرى",
    "Create…": "إنشاء…",
    "Choose a name, variant, and three colors.": "اختر اسمًا ونسخة وثلاثة ألوان.",
    "Right-click a custom theme for options": "انقر بزر الفأرة الأيمن على سمة مخصصة لعرض الخيارات",
    "Create variant…": "إنشاء نسخة…", "Delete theme": "حذف السمة",
    "Delete theme?": "حذف السمة؟", "Theme deleted": "حُذفت السمة",
    "Built-in themes cannot be deleted.": "لا يمكن حذف السمات المدمجة.",
    "Theme not found.": "لم يُعثر على السمة.",
    "Variant": "النسخة", "Create theme": "إنشاء سمة",
    "Theme name": "اسم السمة", "Background color": "لون الخلفية", "Card color": "لون البطاقات", "Accent color": "لون التمييز",
    "Create and use theme": "إنشاء السمة وتفعيلها", "Custom theme created": "تم إنشاء السمة المخصصة",
    "Start with the trigger": "ابدأ بالمُحفّز", "Step 1 · Trigger": "الخطوة ١ · المُحفّز",
    "Choose what starts this shortcut.": "اختر ما يبدأ هذا الاختصار.",
    "Choose a key, mouse button, gesture, or switch. Actions appear after this step.": "اختر مفتاحًا أو زر فأرة أو إيماءة أو مفتاح تبديل. ستظهر الإجراءات بعد هذه الخطوة.",
    "Choose trigger": "اختيار المُحفّز", "Choose a trigger": "اختر مُحفّزًا",
    "Key": "المفتاح", "Default": "افتراضي", "Custom…": "مخصص…",
    "Super": "سوبر", "Ctrl": "تحكم", "Alt": "بديل", "Shift": "إزاحة",
    "Choose a trigger to begin.": "اختر مُحفّزًا للبدء.",
    "Choose a trigger first.": "اختر المُحفّز أولًا.",
    "Continue to actions": "المتابعة إلى الإجراءات",
    "Choose a theme name without path characters.": "اختر اسم سمة بلا رموز مسار.",
    "Choose Light or Dark.": "اختر فاتحًا أو داكنًا.",
    "Use six-digit hex colors such as #4b7f71.": "استخدم ألوانًا سداسية من ست خانات مثل ‎#4b7f71‎.",
    "A theme with this name already exists.": "توجد سمة بهذا الاسم مسبقًا.",
    # Common interface text still visible across pages
    "Add shortcut": "إضافة اختصار", "Search shortcuts or commands…": "ابحث عن اختصارات أو أوامر…",
    "Search…": "بحث…", "+ Layer Rule": "+ قاعدة طبقة",
    "Explore shortcuts on the keyboard": "استعرض الاختصارات على لوحة المفاتيح",
    "APPEARANCE PREVIEW · Illustrative geometry and colors": "معاينة المظهر · شكل وألوان توضيحية",
    "Every documented option rendered from the docs catalog (198 settings). Results update live as you type.": "كل الخيارات الموثقة في الدليل (١٩٨ إعدادًا). تتحدث النتائج أثناء الكتابة.",
    "Mango Default": "افتراضي Mango", "Presets for cycling window widths.": "عروض جاهزة للتنقل بين أحجام النوافذ.",
    "STUDIO": "استوديو", "Options (e.g. grp:alt_shift_toggle, caps:swapescape)": "خيارات مثل grp:alt_shift_toggle وcaps:swapescape",
    # Page titles and frequently used controls
    "Environment Variables": "متغيرات البيئة", "Animations": "الرسوم المتحركة",
    "Window Effects": "تأثيرات النوافذ", "Appearance and Colors": "المظهر والألوان",
    "Raw Config Editor": "محرر الإعدادات النصي", "Outputs & Displays": "المخارج والشاشات",
    "Behavior & Miscellaneous": "السلوك وخيارات متنوعة", "Window & Layer Rules": "قواعد النوافذ والطبقات",
    "Startup & Autostart": "بدء التشغيل والتشغيل التلقائي", "Mouse & Gestures": "الفأرة والإيماءات",
    "Key Bindings": "اختصارات المفاتيح", "Tags & Workspaces": "الوسوم ومساحات العمل",
    "Layout Settings": "إعدادات التخطيط", "Input Devices": "أجهزة الإدخال",
    "Validate": "تحقق", "Revert": "استعادة", "Add Config File": "إضافة ملف إعدادات",
    "Editing File:": "الملف الجاري تعديله:", "Set as Main": "جعله الملف الرئيسي",
    "Search": "بحث", "Close": "إغلاق", "Delete": "حذف", "Remove": "إزالة",
    "Edit": "تعديل", "Add": "إضافة", "Save": "حفظ", "Browse": "استعراض",
    "Shortcuts": "الاختصارات", "Shortcut Details": "تفاصيل الاختصار",
    "Common Presets": "إعدادات شائعة", "Section": "قسم",
    # Appearance and effects
    "Borders and Geometry": "الحدود والشكل", "Window border width and corner rounding": "عرض حدود النوافذ وتدوير الزوايا",
    "Hide Border When Single": "إخفاء الحدود عند وجود نافذة واحدة",
    "Disable border when only one window is visible on tag": "إخفاء الحدود إذا ظهرت نافذة واحدة فقط",
    "Square Corners When Single": "زوايا مربعة عند وجود نافذة واحدة",
    "Disable corner radius when only one window is visible": "إيقاف تدوير الزوايا عند ظهور نافذة واحدة",
    "Window Gaps": "فجوات النوافذ", "Spacing between windows and screen edges": "المسافة بين النوافذ وحواف الشاشة",
    "Smart Gaps": "فجوات ذكية", "Automatically disable gaps when only one window is tiled": "إيقاف الفجوات تلقائيًا عند وجود نافذة مبلطة واحدة",
    "Window and Theme Colors": "ألوان النوافذ والسمة", "Color scheme for borders and indicators": "ألوان الحدود والمؤشرات",
    "Enable Window Blur": "تفعيل ضبابية النوافذ", "Blur Layer Shells": "ضبابية طبقات الواجهة",
    "Apply blur to bars, launchers, and lockscreen": "تطبيق الضبابية على الأشرطة والمشغلات وشاشة القفل",
    "Optimized Blur": "ضبابية محسّنة", "Fast dual-Kawase rendering pass": "معالجة سريعة للضبابية",
    "Enable Window Shadows": "تفعيل ظلال النوافذ", "Shadows on Layer Shells": "ظلال طبقات الواجهة",
    "Shadows Only on Floating Windows": "ظلال للنوافذ العائمة فقط", "Shadow Color": "لون الظل",
    "Opacity and Dimming": "الشفافية والتعتيم", "Translucency and inactive window dimming": "شفافية النوافذ وتعتيم غير النشطة",
    "Enable Inactive Window Dimming": "تعتيم النوافذ غير النشطة",
    # Animation preview remains a first-class Mango feature
    "Animation Configuration": "إعدادات الرسوم المتحركة", "Compositor animation state": "حالة رسوم مدير النوافذ",
    "Enable Window Animations": "تفعيل رسوم النوافذ", "Enable Layer Animations": "تفعيل رسوم الطبقات",
    "Animate rofi, fuzzel, bars, notifications": "تحريك المشغلات والأشرطة والإشعارات",
    "Fade-In on Open": "ظهور تدريجي عند الفتح", "Fade-Out on Close": "اختفاء تدريجي عند الإغلاق",
    "Cubic-Bézier Curve Editor": "محرر منحنى بيزييه", "Visual timing curve with live bouncing particle": "منحنى توقيت مرئي مع معاينة متحركة",
    "Transition Durations (ms)": "مدد الانتقال (مللي ثانية)", "Fine-tune animation speeds": "ضبط سرعة الرسوم المتحركة",
    # Layouts, tags and input
    "Master-Stack Layout": "تخطيط الرئيسي والمكدس", "Classic dwm-style master and slave stack": "نافذة رئيسية ومكدس للنوافذ الأخرى",
    "New Window as Master": "النافذة الجديدة رئيسية", "Spawn newly opened windows in the master area": "وضع النوافذ الجديدة في المنطقة الرئيسية",
    "Scroller Layout": "تخطيط التمرير", "Horizontal scrolling column layout": "تخطيط أعمدة مع تمرير أفقي",
    "Keep Focused Window Centered": "توسيط النافذة النشطة", "Dwindle Layout": "تخطيط التقسيم المتدرج",
    "Binary tree recursive splitting": "تقسيم متكرر على شكل شجرة",
    "Smart Split": "تقسيم ذكي", "Automatically choose split direction by window geometry": "اختيار اتجاه التقسيم حسب شكل النافذة",
    "Manual Split Mode": "وضع التقسيم اليدوي", "Preserve Split": "الحفاظ على التقسيم",
    "Retain split proportion when closing neighbors": "الحفاظ على نسب التقسيم عند إغلاق النوافذ المجاورة",
    "Overview and Scratchpad": "النظرة العامة واللوحة المؤقتة", "Window overview grid and quick scratchpad": "عرض النوافذ واللوحة المؤقتة",
    "Enable Screen Corner Hotarea": "تفعيل زاوية الشاشة", "Trigger overview by moving pointer to corner": "فتح النظرة العامة عند تحريك المؤشر إلى الزاوية",
    "Tag Configuration": "إعدادات الوسوم", "dwm-style tagging system": "نظام الوسوم على نمط dwm",
    "Tag Carousel Loop": "الالتفاف بين الوسوم", "Wrap around when navigating past first or last tag": "العودة إلى أول وسم بعد الأخير والعكس",
    "Tag Gather": "جمع الوسوم", "Gather windows when switching multi-tag views": "جمع النوافذ عند عرض عدة وسوم",
    "Active Monitor Tags (Live IPC)": "وسوم الشاشة النشطة", "Per-Tag Default Layouts": "التخطيطات الافتراضية لكل وسم",
    "Set initial layout algorithm for each tag": "تحديد التخطيط الأولي لكل وسم",
    "Keyboard": "لوحة المفاتيح", "Layout and key repeat settings": "التخطيط وتكرار المفاتيح",
    "Enable NumLock on Startup": "تفعيل NumLock عند البدء", "Trackpad": "لوحة اللمس",
    "Touchpad gestures and clicking": "إيماءات لوحة اللمس والنقر",
    "Disable Trackpad Completely": "تعطيل لوحة اللمس بالكامل", "Tap to Click": "النقر باللمس",
    "Tap and Drag": "اللمس والسحب", "Natural Scrolling": "التمرير الطبيعي",
    "Disable While Typing": "تعطيل أثناء الكتابة", "Left-Handed Mode": "وضع اليد اليسرى",
    "Middle Button Emulation": "محاكاة الزر الأوسط", "Click left and right buttons simultaneously": "النقر بالزرين الأيسر والأيمن معًا",
    "Mouse": "الفأرة", "Pointing device settings": "إعدادات أجهزة التأشير",
    "Cursor and Pointer": "المؤشر", "Cursor appearance and behavior": "مظهر المؤشر وسلوكه",
    "Warp Cursor": "نقل المؤشر", "Warp cursor to newly focused window": "نقل المؤشر إلى النافذة النشطة حديثًا",
    "Hide Cursor on Keypress": "إخفاء المؤشر عند الكتابة",
    # Behavior and rules
    "Focus Behavior": "سلوك التركيز", "Pointer and window activation handling": "طريقة تنشيط النافذة بالمؤشر",
    "Focus Follows Mouse (Sloppy Focus)": "التركيز يتبع الفأرة", "Change focus when pointer hovers over a window": "تنشيط النافذة عند مرور المؤشر فوقها",
    "Focus on Activate": "التركيز عند التنشيط", "Automatically focus windows requesting activation": "تركيز النوافذ التي تطلب التنشيط",
    "Cross-Monitor Focus Navigation": "التنقل بين الشاشات بالتركيز", "Allow directional focus to jump across monitors": "السماح بالتركيز على نوافذ في شاشات أخرى",
    "Cross-Tag Focus Navigation": "التنقل بين الوسوم بالتركيز", "Allow directional focus to switch tags when at edge": "تغيير الوسم عند الوصول إلى الحافة",
    "Dragging and Snapping": "السحب والمحاذاة", "Window drag-to-tile and edge magnetic snap": "سحب النوافذ للتبليط والمحاذاة إلى الحواف",
    "Drag Tile-to-Tile": "سحب نافذة مبلطة إلى أخرى", "Drag a tiled window over another to swap or reorder": "تبديل أو إعادة ترتيب النوافذ المبلطة بالسحب",
    "Floating Window Magnetic Snap": "محاذاة النوافذ العائمة", "Snap floating windows to screen and window edges": "محاذاة النوافذ العائمة إلى الحواف",
    "Power and Idle Inhibit": "الطاقة ومنع الخمول", "Screen lock and sleep prevention": "منع قفل الشاشة والسكون",
    "Inhibit Idle When Fullscreen": "منع الخمول في ملء الشاشة", "Prevent screen sleep when watching fullscreen videos": "منع السكون أثناء مشاهدة فيديو بملء الشاشة",
    "Rendering and Tearing": "العرض وتمزق الصورة", "Low-latency gaming options": "خيارات ألعاب ذات زمن استجابة منخفض",
    "Allow Screen Tearing": "السماح بتمزق الصورة", "Allows unconstrained FPS in games": "السماح بمعدل إطارات غير مقيد في الألعاب",
    "Enable Explicit Sync (syncobj)": "تفعيل المزامنة الصريحة", "Explicit synchronization for modern GPUs / Wayland": "مزامنة بطاقات الرسوم الحديثة وWayland",
    "Window Matching": "مطابقة النوافذ", "Apply Once Only (windowrule-once)": "التطبيق مرة واحدة فقط",
    "Force Floating State": "فرض الوضع العائم", "Force Fullscreen": "فرض ملء الشاشة",
    "Sticky / Pinned Across Tags (isglobal)": "تثبيت عبر الوسوم", "Always On Top (isoverlay)": "دائمًا في المقدمة",
    "Open Silently Without Stealing Focus": "فتح دون سحب التركيز", "Layer Properties": "خصائص الطبقة",
    "Command Setup": "إعداد الأمر", "Run Once at Startup (exec-once)": "تشغيل مرة واحدة عند البدء",
    "Quick Templates": "قوالب سريعة",
    # Catalog sections
    "Keyboard & Typing": "لوحة المفاتيح والكتابة", "Touchscreen": "شاشة اللمس",
    "System & Hardware": "النظام والأجهزة", "Focus & Input": "التركيز والإدخال",
    "Multi-Monitor & Tags": "الشاشات والوسوم", "Window Behavior": "سلوك النوافذ",
    "Theme: Dimensions": "السمة: الأبعاد", "Theme: Colors": "السمة: الألوان",
    "Theme: Overview Jump Labels": "السمة: تسميات التنقل", "Theme: Monocle Tab Bar": "السمة: شريط التبويبات",
    "Theme: Cursor": "السمة: المؤشر", "Effects: Blur": "التأثيرات: الضبابية",
    "Effects: Shadows": "التأثيرات: الظلال", "Effects: Opacity & Radius": "التأثيرات: الشفافية والزوايا",
    "Effects: Dim Overlay": "التأثيرات: التعتيم", "Layouts: Scroller": "التخطيطات: التمرير",
    "Layouts: Master-Stack": "التخطيطات: الرئيسي والمكدس", "Layouts: Dwindle": "التخطيطات: التقسيم المتدرج",
    "Monitor & Tearing": "الشاشات وتمزق الصورة",
    # Dashboard and builder status
    "YOUR WORKSPACE, YOUR RULES": "مساحة عملك، قواعدك",
    "Make room for your flow.": "مساحة تناسب أسلوبك.",
    "Shape how your desktop looks, moves, and feels.": "صمّم مظهر سطح المكتب وحركته وطريقة عمله.",
    "Customize appearance  →": "تخصيص المظهر  →", "Edit configuration": "تعديل الإعدادات",
    "Mango is running": "Mango يعمل", "Offline editing": "التعديل دون اتصال",
    "Your changes can still be saved to the configuration.": "يمكنك حفظ تغييراتك في ملف الإعدادات.",
    "Reload": "إعادة التحميل", "THE CONTROL ROOM": "لوحة التحكم",
    "Look & feel": "المظهر والإحساس", "Colors, borders, blur, and shadows": "الألوان والحدود والضبابية والظلال",
    "Keys & actions": "المفاتيح والإجراءات", "Shortcuts that work the way you do": "اختصارات تناسب أسلوب عملك",
    "Your displays": "شاشاتك", "Resolution, scaling, and arrangement": "الدقة والتحجيم والترتيب",
    "Window layouts": "تخطيطات النوافذ", "Give every window its own place": "مكان مناسب لكل نافذة",
    "Transitions, timing, and curves": "الانتقالات والتوقيت والمنحنيات",
    "Everything ready when you arrive": "كل شيء جاهز عند بدء العمل",
    "CONFIGURATION": "الإعدادات", "Unsaved changes": "تغييرات غير محفوظة",
    "Snapshots": "اللقطات", "Open editor  →": "فتح المحرر  →",
    "Ready to apply. Your configuration is unchanged until you apply.": "جاهز للتطبيق. لن تتغير إعداداتك حتى تضغط تطبيق.",
    "Add an action to start building.": "أضف إجراءً لبدء الإنشاء.",
    "Complete the fields above to generate valid config.": "أكمل الحقول أعلاه لإنشاء إعدادات صالحة.",
    "Resolve the conflict or enable sharing to preview the staged config.": "حل التعارض أو فعّل المشاركة لمعاينة الإعدادات.",
    "No changes to apply.": "لا توجد تغييرات للتطبيق.",
    "No attributes needed": "لا حاجة إلى خصائص",
    "Custom and future commands stay editable without losing their arguments.": "يمكن تعديل الأوامر المخصصة والمستقبلية مع الحفاظ على معاملاتها.",
    "Automatic and Manual Snapshots": "اللقطات التلقائية واليدوية",
    "No backups recorded yet": "لا توجد نسخ احتياطية بعد", "Restore": "استعادة",
    "No saved profiles found": "لا توجد ملفات شخصية محفوظة",
    "MangoMod Shortcuts": "اختصارات MangoMod",
    "Save configuration": "حفظ الإعدادات", "Undo last change": "التراجع عن آخر تغيير",
    "Redo change": "إعادة التغيير", "Reload Mango compositor": "إعادة تحميل Mango",
    "Focus sidebar search": "تركيز البحث في اللوحة الجانبية",
    "Validation Failed": "فشل التحقق", "Save Anyway": "الحفظ رغم ذلك",
})

# The docs-backed catalog supplies many titles and descriptions to several
# pages. Keep their Arabic presentation in one place while leaving config keys,
# enum values and raw arguments byte-for-byte intact.
from mangomod.i18n_catalog import SETTING_LABELS, SECTION_LABELS
from mangomod.mango_settings import SETTINGS

ARABIC.update(SETTING_LABELS)
ARABIC.update(SECTION_LABELS)
ARABIC.update({
    "1 active shortcuts": "اختصار نشط واحد",
    "Actions triggered upon closing or opening laptop lid": "إجراءات عند فتح غطاء الحاسوب أو إغلاقه",
    "Add grain to eliminate banding": "أضف تشويشًا خفيفًا لتقليل تدرج الألوان",
    "Always-on-Top Overlay Border": "حد الطبقة العلوية الدائمة",
    "Animation and effects rules for overlay shells (fuzzel, rofi, waybar, etc.)": "قواعد الرسوم والتأثيرات للطبقات العلوية مثل fuzzel وrofi وwaybar",
    "Assign window movement and actions to mouse clicks": "خصص تحريك النوافذ والإجراءات لنقرات الفأرة",
    "Axis Bindings (Scroll Wheel)": "اختصارات عجلة التمرير",
    "Background blur behind translucent surfaces (scenefx)": "ضبابية الخلفية خلف الأسطح الشفافة",
    "Blur Effects": "تأثيرات الضبابية", "Border Width (px)": "عرض الحدود (بكسل)",
    "Commands executed whenever configuration is reloaded": "أوامر تُنفذ عند كل إعادة تحميل للإعدادات",
    "Commands that run once when Mango compositor starts up": "أوامر تُنفذ مرة عند بدء Mango",
    "Corner Radius (px)": "تدوير الزوايا (بكسل)", "Default Column Proportion": "العرض الافتراضي للعمود",
    "Delay before key begins repeating": "التأخير قبل بدء تكرار المفتاح",
    "Disable Display": "تعطيل الشاشة", "Display Output Name": "اسم مخرج الشاشة",
    "Drag and Drop Target": "هدف السحب والإفلات", "Drop Shadows": "ظلال السحب",
    "Dwindle Split Preview": "معاينة تقسيم التخطيط المتدرج",
    "Ease-In": "تسارع تدريجي", "Ease-Out": "تباطؤ تدريجي",
    "Ease-In-Out": "تسارع وتباطؤ تدريجي", "Linear": "خطي",
    "Custom curve": "منحنى مخصص",
    "Environment variables set before compositor and child processes launch": "متغيرات البيئة قبل تشغيل مدير النوافذ والعمليات التابعة",
    "Focus Switch Duration": "مدة تبديل التركيز", "Focused Window Border": "حد النافذة النشطة",
    "Focused Window Opacity": "شفافية النافذة النشطة", "HDR Support": "دعم HDR",
    "Horizontal outer gap (windows <-> screen edges).": "الفجوة الخارجية الأفقية بين النوافذ وحواف الشاشة.",
    "Inner Horizontal Gap (px)": "الفجوة الداخلية الأفقية (بكسل)",
    "Inner Vertical Gap (px)": "الفجوة الداخلية العمودية (بكسل)",
    "Keep the sibling's split orientation on close.": "احتفظ باتجاه تقسيم النافذة المجاورة عند الإغلاق.",
    "Keys repeated per second": "عدد مرات تكرار المفتاح في الثانية",
    "Laptop Lid Switches": "مفاتيح غطاء الحاسوب",
    "Launch on Every Reload (exec)": "تشغيل عند كل إعادة تحميل (exec)",
    "Launch on Startup (exec-once)": "تشغيل عند البدء (exec-once)",
    "Layer Shell Rules": "قواعد طبقات الواجهة", "Layouts (e.g. us, ara)": "تخطيطات لوحة المفاتيح (مثل us وara)",
    "Live Gesture Previews": "معاينات الإيماءات المباشرة",
    "Map scroll wheel movements with modifiers": "اربط حركة عجلة التمرير بالمفاتيح المعدِّلة",
    "Master Factor (mfact)": "نسبة النافذة الرئيسية (mfact)",
    "Match windows by app-id or title to apply behavior and visual rules": "طابق النوافذ بمعرف التطبيق أو العنوان لتطبيق قواعد السلوك والمظهر",
    "Maximized Window Border": "حد النافذة المكبرة", "Monitor: HDMI-A-1": "الشاشة: HDMI-A-1",
    "Mouse Button Bindings": "اختصارات أزرار الفأرة",
    "Multi-finger swipe gestures for workspace and window navigation": "إيماءات السحب بعدة أصابع للتنقل بين مساحات العمل والنوافذ",
    "No axis bindings configured": "لا توجد اختصارات لعجلة التمرير",
    "No custom environment variables defined": "لا توجد متغيرات بيئة مخصصة",
    "No custom gestures configured": "لا توجد إيماءات مخصصة",
    "No custom mouse button bindings": "لا توجد اختصارات مخصصة لأزرار الفأرة",
    "No layer rules configured": "لا توجد قواعد للطبقات",
    "No lid switch actions configured": "لا توجد إجراءات لغطاء الحاسوب",
    "No reload commands configured": "لا توجد أوامر لإعادة التحميل",
    "No startup commands configured": "لا توجد أوامر لبدء التشغيل",
    "No window rules configured": "لا توجد قواعد للنوافذ",
    "Noise Texture": "نسيج التشويش", "Number of Masters (nmaster)": "عدد النوافذ الرئيسية (nmaster)",
    "Outer Horizontal Gap (px)": "الفجوة الخارجية الأفقية (بكسل)",
    "Outer Vertical Gap (px)": "الفجوة الخارجية العمودية (بكسل)",
    "Pick the split axis from the cursor's position.": "اختر محور التقسيم من موضع المؤشر.",
    "Pinned Global Window Border": "حد النافذة المثبتة على كل الوسوم",
    "Position X (px)": "الموضع الأفقي (بكسل)", "Position Y (px)": "الموضع العمودي (بكسل)",
    "Preset Curve": "منحنى جاهز", "Proportion When Single": "النسبة عند نافذة واحدة",
    "Proportion of screen occupied by master window": "نسبة الشاشة التي تشغلها النافذة الرئيسية",
    "Refresh Rate (Hz)": "معدل التحديث (هرتز)", "Remove Display Configuration": "إزالة إعداد الشاشة",
    "Repeat Delay (ms)": "تأخير التكرار (مللي ثانية)",
    "Resolution Height (px)": "ارتفاع الدقة (بكسل)", "Resolution Width (px)": "عرض الدقة (بكسل)",
    "Root / Desktop Background": "خلفية سطح المكتب", "Scale Factor": "معامل التحجيم",
    "Scratchpad Height Ratio": "نسبة ارتفاع اللوحة المؤقتة", "Scratchpad Width Ratio": "نسبة عرض اللوحة المؤقتة",
    "Scratchpad Window Border": "حد نافذة اللوحة المؤقتة",
    "Session Environment (env=KEY,VALUE)": "متغيرات بيئة الجلسة (env=KEY,VALUE)",
    "Shadow Size (px)": "حجم الظل (بكسل)", "Shadow Softness / Blur (px)": "نعومة الظل وضبابيته (بكسل)",
    "Show interactive animated transition while dragging gestures": "اعرض انتقالًا متحركًا أثناء سحب الإيماءة",
    "Snap Distance (px)": "مسافة المحاذاة (بكسل)", "Spring / Bounce": "نابض وارتداد",
    "Tag / Workspace Switch Duration": "مدة تبديل الوسم أو مساحة العمل",
    "Total tags available per monitor": "إجمالي الوسوم المتاحة لكل شاشة",
    "Trackpad Gestures": "إيماءات لوحة اللمس",
    "Unfocused Window Border": "حد النافذة غير النشطة", "Unfocused Window Opacity": "شفافية النافذة غير النشطة",
    "Urgent Alert Border": "حد التنبيه العاجل", "Variable Refresh Rate (VRR / G-Sync)": "معدل تحديث متغير (VRR / G-Sync)",
    "Variant (optional)": "التنويعة (اختياري)", "Width Presets (comma-separated)": "عروض جاهزة مفصولة بفواصل",
    "Width ratio of newly opened column": "نسبة عرض العمود الجديد",
    "Width ratio when only one window exists": "نسبة العرض عند وجود نافذة واحدة",
    "Window Close Duration": "مدة إغلاق النافذة", "Window Move / Tiling Duration": "مدة تحريك النافذة أو تبليطها",
    "Window Open Duration": "مدة فتح النافذة", "Window Rules": "قواعد النوافذ",
    "Window and layer shadow effects": "تأثيرات ظلال النوافذ والطبقات",
})
for _setting in SETTINGS:
    _label = ARABIC.get(_setting["label"], _setting["label"])
    _kind = _setting["type"]
    if _kind == "bool":
        _description = f"فعّل أو عطّل {_label}."
    elif _kind == "color":
        _description = f"اختر {_label}."
    elif _kind == "enum":
        _description = f"اختر قيمة {_label}."
    elif _kind == "curve":
        _description = "اضبط منحنى توقيت الحركة."
    else:
        _description = f"اضبط قيمة {_label}."
    ARABIC.setdefault(_setting["desc"], _description)

ARABIC.update({
    "Launch Programs": "تشغيل البرامج", "Window Management": "إدارة النوافذ",
    "Focus & Movement": "التركيز والحركة", "Window Groups": "مجموعات النوافذ",
    "Tags & Workspaces": "الوسوم ومساحات العمل", "Monitors & Displays": "الشاشات والمخارج",
    "System": "النظام", "Mouse Actions": "إجراءات الفأرة",
    "Launch an app": "تشغيل تطبيق", "Move a window": "تحريك نافذة",
    "Switch workspace": "تغيير مساحة العمل", "Resize a window": "تغيير حجم نافذة",
    "Toggle floating": "تبديل الوضع العائم", "Change layout": "تغيير التخطيط",
    "Share this keyboard shortcut (adds c to matching bindings in this file)": "مشاركة هذا الاختصار (إضافة c إلى كل اختصار مطابق في الملف الرئيسي)",
    "Execute a program or shell command": "تشغيل برنامج أو أمر صدفة",
    "Run a shell command (supports pipes)": "تشغيل أمر صدفة (يدعم الأنابيب)",
    "Launch an app on an empty tag": "تشغيل تطبيق على وسم فارغ",
    "Load a configuration file from a path": "تحميل ملف إعدادات من مسار",
    "Close the focused window": "إغلاق النافذة النشطة",
    "Toggle floating state": "تبديل الوضع العائم",
    "Float every visible window": "جعل كل النوافذ الظاهرة عائمة",
    "Toggle fullscreen": "تبديل ملء الشاشة",
    "Toggle constrained 'fake' fullscreen": "تبديل ملء الشاشة المقيد",
    "Maximize keeping the bar": "تكبير مع إبقاء الشريط",
    "Pin window across all tags": "تثبيت النافذة على جميع الوسوم",
    "Toggle window border rendering": "تبديل رسم حدود النافذة",
    "Center the floating window": "توسيط النافذة العائمة",
    "Minimize window to scratchpad": "تصغير النافذة إلى اللوحة المؤقتة",
    "Restore minimized window": "استعادة نافذة مصغّرة",
    "Toggle the standard scratchpad": "تبديل اللوحة المؤقتة",
    "Toggle a named scratchpad app": "تبديل تطبيق في لوحة مؤقتة مسماة",
    "Toggle the special overlay workspace": "تبديل مساحة العمل الخاصة",
    "Move window to/from the overlay": "نقل النافذة من وإلى الطبقة الخاصة",
    "Silently move window to/from overlay": "نقل النافذة إلى الطبقة الخاصة دون تركيز",
    "Toggle overlay state of focused window": "تبديل طبقة النافذة النشطة",
    "Toggle the overview grid": "تبديل عرض النوافذ العام",
    "Enter overview mode": "فتح عرض النوافذ العام",
    "Leave overview mode": "إغلاق عرض النوافذ العام",
    "Toggle overview jump mode": "تبديل وضع القفز في عرض النوافذ",
    "Focus a window by client id": "تركيز نافذة برقم العميل",
    "Focus window in a direction": "تركيز نافذة حسب الاتجاه",
    "Focus window, else adjacent tag": "تركيز نافذة أو الانتقال إلى الوسم المجاور",
    "Cycle focus within the stack": "التنقل بين نوافذ المكدس",
    "Open overview / cycle next window": "فتح عرض النوافذ أو الانتقال للنافذة التالية",
    "Focus the previously active window": "تركيز النافذة النشطة سابقًا",
    "Open or cycle the thumbnail switcher": "فتح مبدّل الصور المصغّرة",
    "Swap the focused window with a neighbor": "تبديل النافذة النشطة مع المجاورة",
    "Swap positions within the stack": "تبديل المواضع داخل المكدس",
    "Move the window one step in a direction": "تحريك النافذة خطوة في اتجاه",
    "Swap focused window with Master": "تبديل النافذة النشطة مع الرئيسية",
    "Move floating window by the snap distance": "تحريك نافذة عائمة بمسافة المحاذاة",
    "Resize floating window by the snap distance": "تغيير حجم نافذة عائمة بمسافة المحاذاة",
    "Move floating window by pixels": "تحريك نافذة عائمة بالبكسل",
    "Resize window by pixels": "تغيير حجم النافذة بالبكسل",
    "Join a group by direction": "الانضمام إلى مجموعة حسب الاتجاه",
    "Focus a group member": "تركيز عضو في المجموعة",
    "Leave the current group": "مغادرة المجموعة الحالية",
    "View tag(s) by mask": "عرض الوسوم بالقناع",
    "View previous tag": "عرض الوسم السابق", "View next tag": "عرض الوسم التالي",
    "View or insert an adjacent empty tag": "عرض أو إدراج وسم فارغ مجاور",
    "View left tag and focus a client": "عرض الوسم الأيسر وتركيز نافذة",
    "View right tag and focus a client": "عرض الوسم الأيمن وتركيز نافذة",
    "View previous tag with client": "عرض الوسم السابق الذي يحوي نافذة",
    "View next tag with client": "عرض الوسم التالي الذي يحوي نافذة",
    "View tag(s) on a specific monitor": "عرض الوسوم على شاشة محددة",
    "Move window to tag(s)": "نقل النافذة إلى وسوم",
    "Move window to tag(s) without focusing": "نقل النافذة إلى وسوم دون تركيز",
    "Move window to left tag": "نقل النافذة إلى الوسم الأيسر",
    "Move window to right tag": "نقل النافذة إلى الوسم الأيمن",
    "Move window to tag(s) on a monitor": "نقل النافذة إلى وسوم على شاشة",
    "Toggle tag(s) on the window": "تبديل وسوم النافذة",
    "Toggle view of tag(s)": "تبديل عرض الوسوم",
    "View multiple tags simultaneously": "عرض عدة وسوم معًا",
    "Focus a monitor by direction or spec": "تركيز شاشة حسب الاتجاه أو الاسم",
    "Move window to a monitor": "نقل النافذة إلى شاشة",
    "Turn a monitor's power off": "إطفاء شاشة", "Turn a monitor's power on": "تشغيل شاشة",
    "Toggle a monitor's power": "تبديل طاقة الشاشة",
    "Remove a monitor": "إزالة شاشة", "Add a monitor": "إضافة شاشة",
    "Toggle monitor add/remove": "تبديل إضافة الشاشة أو إزالتها",
    "Toggle HDR on the focused output": "تبديل HDR على الشاشة النشطة",
    "Create a headless monitor": "إنشاء شاشة افتراضية",
    "Destroy all virtual monitors": "إزالة كل الشاشات الافتراضية",
    "Switch to a layout": "التبديل إلى تخطيط",
    "Cycle through layouts": "التنقل بين التخطيطات",
    "Increase / decrease master count": "زيادة أو تقليل عدد النوافذ الرئيسية",
    "Adjust the master area factor": "ضبط مساحة النافذة الرئيسية",
    "Set scroller proportion": "تحديد نسبة تخطيط التمرير",
    "Cycle scroller width presets": "التنقل بين عروض التمرير الجاهزة",
    "Move window in/out of the scroller stack": "نقل النافذة من وإلى مكدس التمرير",
    "Adjust the gap size": "ضبط حجم الفجوات", "Toggle gaps": "تبديل الفجوات",
    "Toggle dwindle split direction": "تبديل اتجاه التقسيم المتدرج",
    "Set dwindle split horizontal": "جعل التقسيم أفقيًا",
    "Set dwindle split vertical": "جعل التقسيم عموديًا",
    "Toggle current window split direction": "تبديل اتجاه تقسيم النافذة الحالية",
    "Hot-reload the configuration": "إعادة تحميل الإعدادات",
    "Exit mango": "إنهاء Mango", "Switch key mode / submap": "تغيير وضع المفاتيح",
    "Cycle or set a keyboard layout": "تغيير تخطيط لوحة المفاتيح",
    "Temporarily set a config option": "تعيين خيار إعدادات مؤقتًا",
    "Toggle enabling the trackpad": "تبديل تفعيل لوحة اللمس",
    "Move or resize a window while dragging (mouse)": "تحريك نافذة أو تغيير حجمها بالسحب",
})


ARABIC.update({
    'Unsaved work': 'عمل غير محفوظ',
    'Save your config changes or discard them before continuing. Unapplied shortcut drafts are kept for recovery.': 'احفظ تغييرات الإعدادات أو تجاهلها قبل المتابعة. تُحفظ مسودات الاختصارات غير المطبقة للاستعادة.',
    'Discard changes': 'تجاهل التغييرات', 'Save and continue': 'احفظ وتابع',
    'Recover draft': 'استعادة المسودة', 'Source file': 'ملف المصدر', 'Default value': 'القيمة الافتراضية',
    'Configuration Valid': 'الإعدادات مقبولة', 'Validation Error': 'خطأ في التحقق',
    'Apply curve to': 'تطبيق المنحنى على', 'Opening windows': 'فتح النوافذ',
    'Closing windows': 'إغلاق النوافذ', 'Moving windows': 'تحريك النوافذ',
    'Switching tags': 'تبديل الوسوم', 'All animations': 'جميع الحركات',
    'Theme options': 'خيارات السمة', 'Available variants': 'الأوضاع المتاحة',
    'Live preview': 'معاينة مباشرة', 'Sample text': 'نص للمعاينة', 'Sample action': 'زر للمعاينة',
    'Text contrast': 'تباين النص', 'Good contrast': 'تباين جيد', 'Low contrast': 'تباين منخفض',
    'Choose a profile name without path characters.': 'اختر اسمًا للملف الشخصي دون رموز المسارات.',
    'A profile with this name already exists.': 'يوجد ملف شخصي بهذا الاسم بالفعل.',
    'Could not restore the configuration. Your recovery snapshot is in Backups.': 'تعذرت استعادة الإعدادات. توجد لقطة الاستعادة في النسخ الاحتياطية.',
    'Integer expected': 'أدخل عددًا صحيحًا', 'Number expected': 'أدخل رقمًا',
    'Reload files from disk': 'إعادة تحميل الملفات من القرص',
    'Some values use preview defaults. Original config values are preserved until edited.': 'تستخدم بعض القيم إعدادات افتراضية للمعاينة. تبقى القيم الأصلية محفوظة حتى تعدّلها.',
    'This curve cannot be previewed. Its original value is preserved until you edit it.': 'لا يمكن معاينة هذا المنحنى. تبقى قيمته الأصلية محفوظة حتى تعدّله.',
    'Restore anyway': 'استعادة على أي حال',
    'This snapshot has no main configuration.': 'لا تحتوي هذه اللقطة على ملف إعدادات رئيسي.',
    'Could not restore the configuration. Check Backups for a recovery snapshot.': 'تعذرت استعادة الإعدادات. راجع النسخ الاحتياطية بحثًا عن لقطة للاستعادة.',
    'Boolean values are 0 or 1': 'القيمة المنطقية هي 0 أو 1',
})


def effective_language(setting: str) -> str:
    if setting == "system":
        name = locale.getlocale()[0] or ""
        return "ar" if name.lower().startswith("ar") else "en"
    return "ar" if setting == "ar" else "en"


def translate(text: str, language: str) -> str:
    if language != "ar":
        return text
    decoded = html.unescape(text)
    if decoded != text:
        return html.escape(translate(decoded, language), quote=False)
    if text in ARABIC:
        return ARABIC[text]
    if match := re.fullmatch(r"(Saved preset|Switched to preset|Deleted preset) '(.+)'", text):
        action = {'Saved preset':'تم حفظ الإعداد المسبق', 'Switched to preset':'تم التبديل إلى الإعداد المسبق', 'Deleted preset':'تم حذف الإعداد المسبق'}[match[1]]
        return f'{action} «{match[2]}»'
    if match := re.fullmatch(r"Delete (.+) and all its saved variants\?", text):
        return f"هل تريد حذف {match[1]} وجميع نسخه المحفوظة؟"
    if match := re.fullmatch(r"This theme has no (Light|Dark) variant\. Create it first\.", text):
        return "لا توجد نسخة " + translate(match[1], language) + " لهذه السمة. أنشئها أولًا."
    if match := re.fullmatch(r"This theme already has a (Light|Dark) variant\.", text):
        return "توجد بالفعل نسخة " + translate(match[1], language) + " لهذه السمة."
    if "\n" in text:
        return "\n".join(translate(part, language) for part in text.split("\n"))
    if text.endswith(("  ↗", "  →")):
        return translate(text[:-3], language) + text[-3:]
    if text.startswith("Version "):
        return "الإصدار " + text[len("Version "):]
    if match := re.fullmatch(r"(\d+) source files  ·  (\d+) snapshots", text):
        return f"{match[1]} ملفات مصدر  ·  {match[2]} لقطات"
    if match := re.fullmatch(r"Action (\d+): (.+)", text):
        return f"الإجراء {match[1]}: {translate(match[2], language)}"
    if match := re.fullmatch(r"Tag (\d+) Default Layout", text):
        return f"التخطيط الافتراضي للوسم {match[1]}"
    if match := re.fullmatch(r"Tag (\d+) \[T\] \((\d+)\)", text):
        return f"الوسم {match[1]} [T] ({match[2]})"
    if match := re.fullmatch(r"(\d+) active shortcuts?", text):
        return f"{match[1]} اختصارات نشطة"
    if text.startswith("Active: "):
        return "السمة النشطة: " + text[8:]
    if match := re.fullmatch(r"Trigger overlaps (\d+) existing binding\(s\): (.+)\. Enable sharing to keep both\.", text):
        return f"يتعارض المُحفّز مع {match[1]} اختصار موجود: {match[2]}. فعّل المشاركة للإبقاء عليهما."
    if match := re.fullmatch(r"Trigger overlaps (\d+) existing binding\(s\): (.+)\. Change the trigger or open the original binding\.", text):
        return f"يتعارض المُحفّز مع {match[1]} اختصار موجود: {match[2]}. غيّر المُحفّز أو افتح الاختصار الأصلي."
    return text


def set_direction(widget: Gtk.Widget, language: str) -> None:
    direction = Gtk.TextDirection.RTL if language == "ar" else Gtk.TextDirection.LTR
    Gtk.Widget.set_default_direction(direction)
    widget.set_direction(direction)


def localize_tree(widget: Gtk.Widget, language: str, _visited=None) -> None:
    """Translate widget labels without changing user-entered config values."""
    if _visited is None:
        _visited = set()
    if widget in _visited:
        return
    _visited.add(widget)
    properties = []
    if widget.get_tooltip_text():
        properties.append(("tooltip", widget.get_tooltip_text, widget.set_tooltip_text))
    if isinstance(widget, Gtk.Label):
        properties.append(("label", widget.get_label, widget.set_label))
    elif isinstance(widget, Gtk.Button) and widget.get_label():
        properties.append(("label", widget.get_label, widget.set_label))
    elif isinstance(widget, Gtk.Expander) and widget.get_label():
        properties.append(("label", widget.get_label, widget.set_label))
    elif isinstance(widget, Gtk.CheckButton) and widget.get_label():
        properties.append(("label", widget.get_label, widget.set_label))
    if isinstance(widget, (Adw.PreferencesRow, Adw.PreferencesGroup)):
        properties.append(("title", widget.get_title, widget.set_title))
        if hasattr(widget, "get_subtitle"):
            properties.append(("subtitle", widget.get_subtitle, widget.set_subtitle))
        if hasattr(widget, "get_description"):
            properties.append(("description", widget.get_description, widget.set_description))
    if isinstance(widget, Adw.WindowTitle):
        properties.append(("title", widget.get_title, widget.set_title))
    if isinstance(widget, Gtk.Window):
        properties.append(("title", widget.get_title, widget.set_title))
    if isinstance(widget, Gtk.Entry) and widget.get_placeholder_text():
        properties.append(("placeholder", widget.get_placeholder_text, widget.set_placeholder_text))
    sources = getattr(widget, "_mm_translation_sources", {})
    for name, get, set_value in properties:
        current = get() or ""
        prior = sources.get(name)
        source = current if prior is None or current != prior[1] else prior[0]
        translated = translate(source, language)
        if translated != current:
            set_value(translated)
        sources[name] = (source, translated)
    widget._mm_translation_sources = sources
    if isinstance(widget, (Gtk.DropDown, Adw.ComboRow)):
        model = widget.get_model()
        if isinstance(model, Gtk.StringList):
            current = [model.get_string(i) for i in range(model.get_n_items())]
            prior = getattr(widget, "_mm_choice_sources", None)
            original = current if prior is None or current != prior[1] else prior[0]
            translated = [translate(item, language) for item in original]
            if translated != current:
                selected = widget.get_selected()
                # Model translation must not invoke editing callbacks.
                signal_id = GObject.signal_lookup('notify', widget.__gtype__)
                blocked = []
                mask = GObject.SignalMatchType.ID | GObject.SignalMatchType.DETAIL | GObject.SignalMatchType.UNBLOCKED
                detail = GLib.quark_from_string('selected')
                while handler := GObject.signal_handler_find(widget, mask, signal_id, detail, None, None, None):
                    widget.handler_block(handler)
                    blocked.append(handler)
                try:
                    widget.freeze_notify()
                    model.splice(0, len(current), translated)
                    widget.set_selected(selected)
                    widget.thaw_notify()
                finally:
                    for handler in blocked:
                        if widget.handler_is_connected(handler):
                            widget.handler_unblock(handler)
            widget._mm_choice_sources = (original, translated)
    if isinstance(widget, Gtk.Expander) and widget.get_child():
        localize_tree(widget.get_child(), language, _visited)
    child = widget.get_first_child()
    while child:
        localize_tree(child, language, _visited)
        child = child.get_next_sibling()

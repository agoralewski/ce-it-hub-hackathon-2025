#!/usr/bin/env python
"""
Script to fix translation files to ensure 'krwinkowy system prezentowy' is never translated.
"""
import os
import re
import polib

# Find all .po files in the project
PO_FILES = [
    '/app/locale/en/LC_MESSAGES/django.po',
    '/app/locale/pl/LC_MESSAGES/django.po'
]

# The string we want to preserve from translation
PRESERVED_STRINGS = [
    'krwinkowy system prezentowy',
    'Krwinkowy System Prezentowy',
    'krwinkowego systemu prezentowego',
    'Krwinkowego Systemu Prezentowego',
    'Krwinkowym Systemie Prezentowym',
    'KSP'
]

def fix_po_file(po_file_path):
    """Fix a .po file to preserve specific strings from translation."""
    po = polib.pofile(po_file_path)
    changes_made = 0
    
    for entry in po:
        for preserved in PRESERVED_STRINGS:
            # Check if the preserved string is in the msgid (in any case)
            if preserved.lower() in entry.msgid.lower():
                # If the string appears in msgid, ensure it's preserved in msgstr
                orig_msgstr = entry.msgstr
                
                # Create a pattern that matches the preserved string case-insensitively
                pattern = re.compile(re.escape(preserved), re.IGNORECASE)
                
                # For English translations, replace "Blood Gift System" with "Krwinkowy System Prezentowy"
                if 'locale/en' in po_file_path and 'Blood Gift System' in entry.msgstr:
                    entry.msgstr = entry.msgstr.replace('Blood Gift System', 'Krwinkowy System Prezentowy')
                    changes_made += 1
                # If the string is already in msgstr but with different case, fix it
                elif pattern.search(entry.msgstr):
                    # This is a bit complex - we need to replace while preserving case
                    for match in pattern.finditer(entry.msgstr):
                        found = match.group(0)
                        for p in PRESERVED_STRINGS:
                            if p.lower() == found.lower():
                                entry.msgstr = entry.msgstr.replace(found, p)
                                break
                    
                    if entry.msgstr != orig_msgstr:
                        changes_made += 1
                # In Polish translation, if msgid and msgstr are the same, no need to change
                elif 'locale/pl' in po_file_path and preserved.lower() in entry.msgid.lower():
                    if not pattern.search(entry.msgstr):
                        # Only replace if needed (preserve case)
                        match = re.search(re.escape(preserved), entry.msgid, re.IGNORECASE)
                        if match:
                            found = match.group(0)
                            entry.msgstr = entry.msgstr if entry.msgstr else entry.msgid
                            changes_made += 1
    
    if changes_made > 0:
        po.save()
        print(f"Fixed {changes_made} translations in {po_file_path}")
    else:
        print(f"No changes needed in {po_file_path}")

def main():
    """Main function to fix all translation files."""
    for po_file_path in PO_FILES:
        if os.path.exists(po_file_path):
            print(f"Processing {po_file_path}...")
            fix_po_file(po_file_path)
        else:
            print(f"File not found: {po_file_path}")

if __name__ == "__main__":
    main()

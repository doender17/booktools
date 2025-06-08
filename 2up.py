import argparse
import subprocess
import sys
from PyPDF2 import PdfReader

def get_pdf_info(file_path):
    reader = PdfReader(file_path)
    num_pages = len(reader.pages)

    # Check the size and orientation of the first page
    first_page = reader.pages[0]
    width = float(first_page.mediabox.width)
    height = float(first_page.mediabox.height)

    orientation = "landscape" if width > height else "portrait"

    return {
        "file": file_path,
        "pages": num_pages,
        "width_pt": width,
        "height_pt": height,
        "orientation": orientation
    }


def run_pdfjam(input_file, output_file, page_order, nup, papersize, orientation):
    cmd = [
        "pdfjam",
        input_file,
	page_order,
        "--nup", nup,
        "--papersize", papersize,
        "--outfile", output_file
    ]

    if orientation == "landscape":
        cmd.append("--landscape")
    else:
        cmd.append("--portrait")

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error running pdfjam:")
        print(result.stderr)
        sys.exit(result.returncode)
    else:
        print("Success:")
        print(result.stdout)

def booklet_signatures_order(num_pages, pages_per_signature=16):
    """
    Divide pages into signatures (booklets) for binding.
    Each signature has a multiple of 4 pages (default 16 pages = 4 sheets).
    Returns a list of page numbers (or None for blanks) in correct order.
    """
    signatures = []
    current_page = 1

    while current_page <= num_pages:
        # Pages in this signature
        remaining = num_pages - current_page + 1
        sig_size = min(pages_per_signature, remaining)

        # Round up to multiple of 4
        padded_size = ((sig_size + 3) // 4) * 4
        pages = list(range(current_page, current_page + sig_size))
        pages += [None] * (padded_size - sig_size)

        sig_order = []
        total = len(pages)
        for i in range(0, total // 2, 2):
            left = total - i - 1
            right = i
            inner_left = i + 1
            inner_right = total - i - 2
            sig_order.extend([pages[left], pages[right], pages[inner_left], pages[inner_right]])

        signatures.append(sig_order)
        current_page += sig_size

    # Flatten the list of signatures
    return [page for sig in signatures for page in sig]

def page_order_signature_no_duplex(num_pages):
    # Signature booklets, all pages ordered for no-duplex printing
    # Print half the number of pages first
    # Then put printed pages back in the printer paper feed
    # do not reorder anything
    # Print the second half of the pages
    order = booklet_signatures_order(num_pages)
    print(order)
    reordered = []
    # Print all the even ones
    l = len(order)
    for i in range(l//4):
       reordered.append(order[i*4])
       reordered.append(order[i*4 + 1])

    # Print all the odd ones in reverse order
    for i in range(l//4):
       reordered.append(order[l - i*4 - 2])
       reordered.append(order[l - i*4 - 1])

    print(reordered)
    return reordered

def booklet_signatures_order(num_pages, pages_per_signature=16):
    """
    Divide pages into signatures (booklets) for binding.
    Each signature has a multiple of 4 pages (default 16 pages = 4 sheets).
    Returns a list of page numbers (or None for blanks) in correct order.
    """
    signatures = []
    current_page = 1

    while current_page <= num_pages:
        # Pages in this signature
        remaining = num_pages - current_page + 1
        sig_size = min(pages_per_signature, remaining)

        # Round up to multiple of 4
        padded_size = ((sig_size + 3) // 4) * 4
        pages = list(range(current_page, current_page + sig_size))
        pages += [None] * (padded_size - sig_size)

        sig_order = []
        total = len(pages)
        for i in range(0, total // 2, 2):
            left = total - i - 1
            right = i
            inner_left = i + 1
            inner_right = total - i - 2
            sig_order.extend([pages[left], pages[right], pages[inner_left], pages[inner_right]])

        signatures.append(sig_order)
        current_page += sig_size

    # Flatten the list of signatures
    return [page for sig in signatures for page in sig]

def main():
    parser = argparse.ArgumentParser(description="Wrap pdfjam to create 2-up or other layouts.")
    parser.add_argument("input", help="Input PDF file")
    parser.add_argument("output", help="Output PDF file")
    parser.add_argument("--nup", default="2x1", help="Page layout in format NxM (default: 2x1)")
    parser.add_argument("--paper", default="a4paper", help="Paper size (default: a4paper)")

    args = parser.parse_args()

    info = get_pdf_info(args.input)

    target_orientation = 'portrait'
    papersize = "{%spt, %spt}" % (2.0 * info["width_pt"], info["height_pt"])
    if info["orientation"].lower() == 'portrait':
       target_orientation = 'landscape'
       papersize = "{%spt, %spt}" % (info["height_pt"], 2.0*info["width_pt"])

    pages = page_order_signature_no_duplex(info["pages"])
    pages = ["%s" %p for p in pages]
    pages = ",".join(pages).replace("None", "{}")
    run_pdfjam(
        args.input,
        args.output,
        pages,
        "2x1",
        papersize,
        target_orientation
    )

if __name__ == "__main__":
    main()

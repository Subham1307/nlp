import os

class FileHandler:
    @staticmethod
    def ensure_directory_exists(directory):
        """Ensure that a directory exists, create it if it doesn't"""
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def write_merged_output(output_folder, all_notes, all_texts):
        """Write merged output to a file"""
        merged_file = os.path.join(output_folder, "all_pages_merged.txt")
        with open(merged_file, 'w', encoding='utf-8') as f:
            f.write("**NOTES:**\n")
            f.write("\n".join(all_notes))
            f.write("\n\n**TEXTS:**\n")
            f.write("\n".join(all_texts))
        return merged_file 
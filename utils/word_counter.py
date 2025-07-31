# ------------------------------------------------------------------------------------------
#
# market-def-scraper - Extracts market definitions from European Commission's decision PDFs
#
# Copyright (C) 2025 Shriyan Yamali
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Contact: yamalishriyan@gmail.com
#
# ------------------------------------------------------------------------------------------

def count_words(file_path):
    count = 0
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            words = line.split(" ")
            count += len(words)
    print("Number of words present in given file: " + str(count))
    return count

if __name__ == "__main__":
    count_words("") # specify the path to your file

#!/bin/sh

set -eu

read -p "Enter a name for the exercise (used for tag name): " exercise_name

read -p "Are you sure you want to create a new tag? This will cause a new tag to be created in each student project and run JPlag on the solutions. [N/y]: " cont

if [ ${cont} == 'y' ] || [ ${cont} == 'Y' ]
then
	git tag "${exercise_name}"
	git push --tag
fi

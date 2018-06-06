#!/bin/sh

for d in $(cat abgaben.txt)
do
	time=$(echo $d | cut -d',' -f1)
	tag=$(echo $d | cut -d',' -f2)
	now=$(date --iso-8601)

	if [[ "$time" < "$now" ]] || [[ "$time" = "$now" ]]
	then
		git tag ${tag}
		git push --tags
	fi
done

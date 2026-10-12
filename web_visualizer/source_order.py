"""Sort selected sentences by their original input position, retaining a trace."""
def sort_by_input(sentences):
    before = [dict(sentence) for sentence in sentences]
    after = sorted(before, key=lambda sentence: sentence["sourceIndex"])
    before_order = {sentence["id"]: index for index, sentence in enumerate(before, 1)}
    after_order = {sentence["id"]: index for index, sentence in enumerate(after, 1)}
    output = []
    for index, sentence in enumerate(after, 1):
        output.append({**sentence, "order": index, "displayOrder": index})
    return output, {
        "before": [{**sentence, "beforeOrder": index, "afterOrder": after_order[sentence["id"]]}
                   for index, sentence in enumerate(before, 1)],
        "after": [{**sentence, "beforeOrder": before_order[sentence["id"]], "afterOrder": index}
                  for index, sentence in enumerate(after, 1)],
        "changed": [sentence["id"] for sentence in before] != [sentence["id"] for sentence in after],
    }

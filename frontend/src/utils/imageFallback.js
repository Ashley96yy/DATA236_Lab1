export function getFallbackRestaurantImage(cuisine, tags = []) {
  const c = (cuisine || "").toLowerCase();
  const allTags = Array.isArray(tags) ? tags.map(t => t.toLowerCase()).join(" ") : "";
  const text = `${c} ${allTags}`;

  if (/(chinese|sichuan|cantonese)/.test(text)) return "/images/default-chinese.jpg";
  if (/(japanese|sushi|ramen)/.test(text)) return "/images/default-japanese.jpg";
  if (/(mexican|taco|cantina)/.test(text)) return "/images/default-mexican.jpg";
  if (/(italian|pizza|pasta)/.test(text)) return "/images/default-italian.jpg";
  if (/(american|steakhouse|bbq|burger)/.test(text)) return "/images/default-american.jpg";
  if (/(cafe|coffee|bakery|brunch)/.test(text)) return "/images/default-cafe.jpg";

  return "/images/default-generic.jpg";
}

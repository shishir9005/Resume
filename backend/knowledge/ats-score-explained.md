# How the ATS Resume Scorer Works

## The five score components
The ATS Resume Scorer gives a score from 0 to 100 built from five components: Formatting (up to 20 points), Keywords and Skills (up to 25), Content Quality (up to 25), Skill Validation (up to 15), and ATS Compatibility (up to 15). Each component is converted to a percentage and combined into the overall score, with small bonuses and penalties applied at the end.

## Formatting score
Formatting rewards a complete structure: an Experience section with content, an Education section, at least three skills, a professional summary longer than a sentence, and a Projects section. It also counts bullet points; around 15 or more bullets earns the full bullet credit. To raise it, add any missing standard section and write content as bullet points rather than paragraphs.

## Keywords and skills score
This counts the resume's extracted keywords (20 or more earns full credit) and listed skills (15 or more earns full credit). When a job description is provided, it also measures what share of the job's keywords appear in the resume, using fuzzy matching so small spelling differences still count. To raise it, add relevant, honest skills and the job description's missing keywords.

## Content quality score
Content quality has three parts. Strong action verbs at the start of bullets are worth up to 10 points (15 or more verbs earns full credit). Quantified achievements such as percentages, money amounts, counts of users or projects, and phrases like "increased by 20" are worth up to 5 points (about 10 measurable results earns full credit). Grammar is worth up to 10 points; grammar checking is currently unavailable, so every resume receives full grammar credit. To raise this score, rewrite weak bullets with action verbs and add honest numbers.

## Skill validation score
For each listed skill, the scorer checks whether a project or experience entry mentions it directly or is semantically similar to it, using sentence embeddings. The score is the validated share of skills times 15. Validating 80% or more of skills also earns a bonus. To raise it, show each listed skill in a project or job bullet, or remove skills you cannot support.

## ATS compatibility score and penalties
ATS compatibility starts at 15 and loses points for detailed location information (street address or ZIP code), many decorative box-drawing characters, and sections that are nearly empty. When a job description is provided, missing more than 30% of its keywords applies a penalty of 5 points, rising to 10 above 50% missing and 15 above 70% missing. This is often the biggest single reason a JD comparison score is low.

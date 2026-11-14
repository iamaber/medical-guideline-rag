# Data licences and attribution

The application code is MIT-licensed in [LICENSE](LICENSE). This notice covers
third-party data separately; it does not grant the MIT licence to that data.

## WHO documents and derived material

The eight WHO PDFs listed below and material derived from them are provided under
[Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO (CC BY-NC-SA 3.0 IGO)](https://creativecommons.org/licenses/by-nc-sa/3.0/igo/).
Use is **non-commercial only**. Cite WHO and the individual work using the
suggested citations below, retain the notices, and link the licence. Adaptations
must be shared under the same or an equivalent Creative Commons licence. This
project is not endorsed by WHO; the WHO logo may not be used.

In the Space the PDFs are in `data/raw/`; in the GitHub source repository they
are in `backend/data/raw/`. The same relative mapping applies to the following
files. This notice applies to WHO-derived content in `data/processed/*.json`
(in particular `who_guidelines.json`), `data/documents_metadata.json` and
`data/vector_index.faiss`. The PDFs are redistributed unchanged. The pipeline
extracts and cleans text, creates summaries and metadata, and embeds content for
retrieval; those derivative representations are not official WHO publications.
The index and metadata also mix in PubMed content, whose separate rights are
not granted by the WHO licence (see Other third-party data below).

WHO's copyright pages state:

> Under the terms of this licence, you may copy, redistribute and adapt the work for non-commercial purposes, provided the work is appropriately cited, as indicated below. In any use of this work, there should be no suggestion that WHO endorses any specific organization, products or services. The use of the WHO logo is not permitted. If you adapt the work, then you must license your work under the same or equivalent Creative Commons licence.

For the self-monitoring blood-pressure Digital Adaptation Kit, WHO expressly
requires this disclaimer for translations **or adaptations**; it is reproduced
here for the project's derivative material along with that work's citation:

> This translation/adaptation was not created by the World Health Organization (WHO). WHO is not responsible for the content or accuracy of this translation/adaptation. The original English edition shall be the binding and authentic edition.

The other seven copyright pages supply the following translation disclaimer,
which must accompany any translation and its suggested citation:

> This translation was not created by the World Health Organization (WHO). WHO is not responsible for the content or accuracy of this translation. The original English edition shall be the binding and authentic edition.

The PDFs also retain WHO's general disclaimers, including:

> All reasonable precautions have been taken by WHO to verify the information contained in this publication. However, the published material is being distributed without warranty of any kind, either expressed or implied. The responsibility for the interpretation and use of the material lies with the reader. In no event shall WHO be liable for damages arising from its use.

Any mediation relating to disputes under the licence follows the mediation rules
of the World Intellectual Property Organization, as stated in the PDFs. Requests
for commercial use and rights queries: <https://www.who.int/copyright>.

## Individual WHO works

The following are quotations extracted from the bundled PDFs with
`pdftotext -layout`; line wrapping is normalized. Titles and years come from
the PDFs, rather than the shortened filenames. All eight copyright pages state
**© World Health Organization 2025**. Each suggested citation below supplies
the required author/publisher attribution, title, year and licence.

### 1. Clinical management and infection prevention and control for mpox: living guideline, May 2025 (2025)

Bundled filename: `Clinical management and infection prevention and control for mpox.pdf`. Copyright/licensing notice: PDF page 4.

> © World Health Organization 2025
>
> Some rights reserved. This work is available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO licence (CC BY-NC-SA 3.0 IGO; https://creativecommons.org/licenses/by-nc-sa/3.0/igo).
>
> Suggested citation. Clinical management and infection prevention and control for mpox: living guideline, May 2025. Geneva: World Health Organization; 2025. https://doi.org/10.2471/B09434. Licence: CC BY-NC-SA 3.0 IGO.

### 2. WHO guidelines for clinical management of arboviral diseases: dengue, chikungunya, Zika and yellow fever (2025)

Bundled filename: `Clinical management of arboviral diseases:dengue, chikungunya, Zika and yellow fever.pdf`. Copyright/licensing notice: PDF page 4.

> © World Health Organization 2025
>
> Some rights reserved. This work is available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO licence (CC BY-NC-SA 3.0 IGO; https://creativecommons.org/licenses/by-nc-sa/3.0/igo).
>
> Suggested citation. WHO guidelines for clinical management of arboviral diseases: dengue, chikungunya, Zika and yellow fever. Geneva: World Health Organization; 2025. Licence: CC BY-NC-SA 3.0 IGO.

### 3. Health system strengthening interventions to improve the health of displaced and migrant populations in the context of climate change (2025)

Bundled filename: `Health system strengthe Health of displaced and migrant populations in the context of climate change.pdf`. Copyright/licensing notice: PDF page 4.

> © World Health Organization 2025
>
> Some rights reserved. This work is available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO licence (CC BY-NC-SA 3.0 IGO; https://creativecommons.org/licenses/by-nc-sa/3.0/igo).
>
> Suggested citation. Health system strengthening interventions to improve the health of displaced and migrant populations in the context of climate change. Geneva: World Health Organization; 2025 (Global Evidence Review on Health and Migration (GEHM) series). Licence: CC BY-NC-SA 3.0 IGO.

### 4. Guidelines on lenacapavir for HIV prevention and testing strategies for long-acting injectable pre-exposure prophylaxis (PrEP) (2025)

Bundled filename: `Lenacapavir for HIV prevention and testing strategies.pdf`. Copyright/licensing notice: PDF page 4.

> © World Health Organization 2025
>
> Some rights reserved. This work is available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO licence (CC BY-NC-SA 3.0 IGO; https://creativecommons.org/licenses/by-nc-sa/3.0/igo).
>
> Suggested citation. Guidelines on lenacapavir for HIV prevention and testing strategies for long-acting injectable pre-exposure prophylaxis (PrEP). Geneva: World Health Organization; 2025. Licence: CC BY-NC-SA 3.0 IGO.

### 5. Guidelines for the management of asymptomatic sexually transmitted infections (2025)

Bundled filename: `Management of asymptomatic sexually transmitted infections.pdf`. Copyright/licensing notice: PDF page 4.

> © World Health Organization 2025
>
> Some rights reserved. This work is available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO licence (CC BY-NC-SA 3.0 IGO; https://creativecommons.org/licenses/by-nc-sa/3.0/igo).
>
> Suggested citation. Guidelines for the management of asymptomatic sexually transmitted infections. Geneva: World Health Organization; 2025. Licence: CC BY-NC-SA 3.0 IGO.

### 6. WHO recommendations on the management of sickle cell disease during pregnancy, childbirth and the interpregnancy period (2025)

Bundled filename: `Management of sickle-cell disease during pregnancy, childbirth and the interpregnancy period.pdf`. Copyright/licensing notice: PDF page 4.

> © World Health Organization 2025
>
> Some rights reserved. This work is available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO licence (CC BY-NC-SA 3.0 IGO; https://creativecommons.org/licenses/by-nc-sa/3.0/igo).
>
> Suggested citation. WHO recommendations on the management of sickle cell disease during pregnancy, childbirth and the interpregnancy period. Geneva: World Health Organization; 2025. Licence: CC BY-NC-SA 3.0 IGO.

### 7. Digital adaptation kit for self-monitoring of blood pressure during pregnancy: operational requirements for implementing WHO recommendations in digital systems (2025)

Bundled filename: `Self-monitoring of blood pressure during pregnancy.pdf`. Copyright/licensing notice: PDF page 4.

> © World Health Organization 2025
>
> Some rights reserved. This work is available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO licence (CC-BY-NC-SA-3.0-IGO https://creativecommons.org/ licenses/by-nc-sa/3.0/igo/).
>
> Suggested citation. Digital adaptation kit for self-monitoring of blood pressure during pregnancy: operational requirements for implementing WHO recommendations in digital systems. Geneva: World Health Organization; 2025 (SMART Guidelines collection). https://iris.who.int/handle/10665/381616. Licence: CC BY-NC-SA 3.0 IGO.

### 8. WHO guidelines for the treatment of patients with cystic echinococcosis (2025)

Bundled filename: `Treatment of patients with cystic echinococcosis.pdf`. Copyright/licensing notice: PDF page 4.

> © World Health Organization 2025
>
> Some rights reserved. This work is available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO licence (CC BY-NC-SA 3.0 IGO; https://creativecommons.org/licenses/by-nc-sa/3.0/igo).
>
> Suggested citation. WHO guidelines for the treatment of patients with cystic echinococcosis. Geneva: World Health Organization; 2025. Licence: CC BY-NC-SA 3.0 IGO.

## Embedded third-party material and exceptions

Each WHO copyright page warns (line wrapping normalized):

> Third-party materials. If you wish to reuse material from this work that is attributed to a third party, such as tables, figures or images, it is your responsibility to determine whether permission is needed for that reuse and to obtain permission from the copyright holder. The risk of claims resulting from infringement of any third-party-owned component in the work rests solely with the user.

The following credits were found in the extracted text. Page numbers below are
**PDF file pages**, including front matter. They do not replace the credits in
the documents or grant new rights to the credited material.

In *WHO guidelines for the treatment of patients with cystic echinococcosis*:

- PDF page 16, Figure 3 cyst-classification images: “© Francesca Tamarozzi”. No separate reuse licence is specified alongside that credit.
- PDF page 22: “Watching the flock, Mongolia © European Union / Pierre Prakash; Licence CC BY-NC-ND 2.0”.
- PDF page 38: “Peruvian farmers with their sheep © Shawn Harquail; Licence CC BY-NC-ND 2.0”.
- PDF page 42: “Young boy with sheep - Ethiopia, 2016 © ILRI / Camille Hanotte; Licence CC BY-NC-ND 2.0”.
- PDF page 45: “A shepherd dog and its flock, Sardinia © Marshall Lightowlers.” No separate reuse licence is specified alongside that credit.

The three CC BY-NC-ND 2.0 images retain that licence, including its
**NoDerivatives** restriction; the project's CC BY-NC-SA notice does not
relicense them or permit adaptations of those images. See the
[CC BY-NC-ND 2.0 terms](https://creativecommons.org/licenses/by-nc-nd/2.0/).

In *WHO recommendations on the management of sickle cell disease during
pregnancy, childbirth and the interpregnancy period*, Figure 1 (PDF page 18)
states “Diagram adapted from Joseph L, et., al (3).” No separate reuse licence
is specified there. Its copyright page credits “Cover photo: Sickle-cell
disease red blood cells in motion. Freepik AI Image Generator.” Do not infer
an independent licence for those components from the WHO-wide notice.

The arboviral guidelines credit material on PDF pages 18–19 as “Adapted from
the Pan American Health Organization guidelines for diagnosis and treatment
of dengue, chikungunya, and zika in the Region of the Americas”; reference 2
identifies that PAHO work as “License: CC BY-NC-SA 3.0 IGO.” The health-system
review credits its map to “the WHO GIS Centre for Health DNA/DDI. © WHO 2025;
Licence: CC BY-NC-SA 3.0 IGO” and says its illustrations on pages 1, 7, 17 and
32 were generated using MidJourney and refined using Photoshop. These are
credits in the PDFs, not additional licences granted by this project.

The Digital Adaptation Kit's diagram credits WHO (12). No additional specific
third-party reuse licence was found in the extracted mpox, asymptomatic-STI,
lenacapavir or blood-pressure-kit text. All retain the general third-party
warning above. Cited external publications retain their own terms; a reference
alone does not relicense their content. This text extraction is not a complete
clearance of embedded artwork or every externally cited work.

## Other third-party data

- **MedEx Bangladesh drug-brand lookup:** `data/drug_db/medex_URL.json` contains
  22,974 brand names and URLs and records a scrape timestamp of
  `2025-08-18 22:58:55`. `src/data_collection/fetch_medex.py` identifies its source
  as <https://medex.com.bd/brands>, retrieved through <https://r.jina.ai/>.
  `config/settings.py` points to this file and `src/services/drug_lookup.py`
  loads it at startup; the application can also retrieve linked monographs.
  The repository supplies no redistribution licence or permission for this
  scraped database or the MedEx monographs. Their terms remain **unverified**;
  this notice assigns them neither MIT nor the WHO licence.
- **PubMed literature:** `src/data_collection/fetch_pubmed.py` fetches article
  titles/abstracts using NCBI Entrez and stores source URLs of the form
  `https://pubmed.ncbi.nlm.nih.gov/<PMID>/`. There are 33 non-WHO JSON files in
  `data/processed/`, alongside `who_guidelines.json`. The bundled metadata has
  12,457 `pubmed_article` records and 8 `who_guideline` records (records include
  separate article sections, not necessarily distinct articles). PubMed-derived
  abstracts, metadata and index entries are **not** relicensed as WHO material.
  No uniform article-level licence or redistribution permission is documented
  in these files; check the original publishers' terms. The mixed index does
  not establish a new licence for these separate contributions.

The owner must establish any outstanding permissions before relying on these
other sources' redistribution rights. The MIT code licence remains separate
from all of the third-party data described here.

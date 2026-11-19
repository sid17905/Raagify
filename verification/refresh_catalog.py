"""Refresh imported metadata and pending audio features without replacing curated genres."""

import json
import httpx
from runtime import ROOT, credentials


def main():
    private = credentials()
    with httpx.Client(base_url="http://127.0.0.1:18080/api", timeout=90) as client:

        def csrf():
            return {"X-XSRF-TOKEN": client.get("/auth/csrf").json()["token"]}

        assert (
            client.post(
                "/auth/login",
                headers=csrf(),
                data={
                    "email": "private-admin@raagify.test",
                    "password": private["adminPassword"],
                },
            ).status_code
            == 200
        )
        first = client.get("/songs?size=50&page=0").json()
        catalog = list(first["content"])
        for page in range(1, first["totalPages"]):
            catalog += client.get(f"/songs?size=50&page={page}").json()["content"]
        result = {
            "classification": "Observed",
            "metadataRefreshed": 0,
            "featuresRefreshed": 0,
            "adminOverridesPreserved": 0,
            "failed": [],
            "songCount": len(catalog),
        }
        for index, song in enumerate(catalog):
            response = client.post(
                f"/admin/songs/{song['id']}/metadata/refresh", headers=csrf()
            )
            if response.status_code != 200:
                result["failed"].append(
                    {
                        "id": song["id"],
                        "step": "metadata",
                        "status": response.status_code,
                    }
                )
                continue
            updated = response.json()
            result["metadataRefreshed"] += 1
            if song["genreSource"] == "ADMIN_OVERRIDE":
                assert (
                    updated["genre"] == song["genre"]
                    and updated["genreSource"] == "ADMIN_OVERRIDE"
                )
                result["adminOverridesPreserved"] += 1
            elif (
                song["genreSource"] in ("PENDING", "UNCLASSIFIED")
                or song["featureStatus"] == "PENDING"
            ):
                prediction = client.post(
                    f"/admin/songs/{song['id']}/features/retry", headers=csrf()
                )
                if (
                    prediction.status_code == 200
                    and prediction.json()["featureStatus"] == "READY"
                ):
                    result["featuresRefreshed"] += 1
                else:
                    result["failed"].append(
                        {
                            "id": song["id"],
                            "step": "features",
                            "status": prediction.status_code,
                        }
                    )
            print(
                f"Observed: refreshed {index + 1}/{len(catalog)}; audio features refreshed={result['featuresRefreshed']}",
                flush=True,
            )
        (ROOT / "verification/catalog-refresh.json").write_text(
            json.dumps(result, indent=2)
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()

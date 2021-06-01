import requests


class QmaticOrchestraCalendarClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def __str__(self):
        return f"{self.__class__.__name__}({self.base_url})"

    def book_appointment(self, branch_public_id, service_public_id, date, time):
        url = (
            "{}/calendar-backend/public/api/v1/branches/{}/services/{}/dates/{}/times/{}/book"
        ).format(self.base_url, branch_public_id, service_public_id, date, time)

        # TODO data should be retrieved from form
        response = requests.post(
            url,
            json={
                "title": "Online booking",
                "customer": {
                    "firstName": "Voornaam",
                    "lastName": "Achternaam",
                    "email": "test@test.com",
                    "phone": "06-11223344",
                    "addressLine1": "Straatnaam 1",
                    "addressCity": "Plaatsnaam",
                    "addressState": "Zuid Holland",
                    "addressZip": "1111AB",
                    "addressCountry": "Nederland",
                    "identificationNumber": "1234567890",
                    "dateOfBirth": "1900-01-31",
                },
                "notes": "Geboekt via internet",
            },
        )
        return response

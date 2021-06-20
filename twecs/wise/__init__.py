import logging
import uuid

import requests

logger = logging.getLogger(
    __name__,
)


def set_up_transfer(
        amount,
        amount_side,
        api_key,
        base_url,
        reference,
        source_currency,
        target_currency,
    ):
    session = requests.Session(
    )

    session.hooks['response'].append(
        request_response_hook,
    )

    session.headers['Authorization'] = 'Bearer ' + api_key

    response = session.get(
        f'{base_url}/v1/profiles',
    )

    if response.status_code == requests.codes.ok:
        profiles = response.json(
        )

        personal_profile_id = None

        for profile in profiles:
            if profile['type'] == 'personal':
                personal_profile_id = profile['id']

                logger.debug(
                    'ID of personal profile: %i',
                    personal_profile_id,
                )

                break

        assert personal_profile_id

        profile_id = personal_profile_id

        logger.debug(
            'using profile ID %i',
            profile_id,
        )

        response = session.get(
            f'{base_url}/v1/borderless-accounts',
            params={
                'profileId': profile_id,
            },
        )

        response_data = response.json(
        )

        response_data_item = response_data[0]

        recipient_id = response_data_item['recipientId']

        request_json = {
            'preferredPayIn': 'BANK_TRANSFER',
            'profile': profile_id,
            'sourceCurrency': source_currency,
            'targetCurrency': target_currency,
            'targetAccount': recipient_id,
        }

        if amount_side == 'source':
            request_json['sourceAmount'] = amount
        else:
            assert amount_side == 'target'
            request_json['targetAmount'] = amount

        response = session.post(
            f'{base_url}/v2/quotes',
            headers={
                'Content-Type': 'application/json',
            },
            json=request_json,
        )

        if response.status_code == requests.codes.ok:
            data = response.json(
            )

            quote_id = data['id']

            logger.debug(
                'quote ID: %s',
                quote_id,
            )

            logger.info(
                'rate reported by Wise: %f',
                data['rate'],
            )

            payment_options = data['paymentOptions']

            source_amount_via_transfer = None
            target_amount = None
            if amount_side == 'target':
                target_amount = amount

            for payment_option in payment_options:
                if payment_option['payIn'] == 'BANK_TRANSFER':
                    source_amount_via_transfer = payment_option['sourceAmount']
                    if amount_side == 'source':
                        target_amount = payment_option['targetAmount']
                    break

            assert source_amount_via_transfer

            logger.info(
                'source amount when funding via bank transfer: %f',
                source_amount_via_transfer,
            )

            transfer_creation_uuid = uuid.uuid4(
            )
            transfer_creation_identifier = str(
                transfer_creation_uuid,
            )

            transfer_id = None

            should_try = True
            while should_try:
                response = session.post(
                    f'{base_url}/v1/transfers',
                    headers={
                        'Content-Type': 'application/json',
                    },
                    json={
                        'customerTransactionId': transfer_creation_identifier,
                        'details': {
                            'reference': reference,
                        },
                        'quoteUuid': quote_id,
                        'targetAccount': recipient_id,
                    },
                )

                if response.status_code == requests.codes.ok:
                    response_data = response.json(
                    )

                    transfer_id = response_data['id']

                    should_try = False
                else:
                    should_try = True

            transfer = {
                'reference': reference,
                'source_amount_via_transfer': source_amount_via_transfer,
                'source_currency': source_currency,
                'target_amount': target_amount,
                'target_currency': target_currency,
                'id': transfer_id,
            }

            return transfer


def request_response_hook(
        response,
        *args,
        **kwargs,
    ):
    logger.debug(
        'response: %s',
        response.text,
    )

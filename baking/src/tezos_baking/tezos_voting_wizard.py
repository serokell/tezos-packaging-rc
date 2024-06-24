#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

"""
A wizard utility to help with voting on the Tezos protocol.

Asks questions, validates answers, and executes the appropriate steps using the final configuration.
"""

import os, sys
import readline
import logging
import re

from tezos_baking.wizard_structure import *
from tezos_baking.util import *
from tezos_baking.steps import *
from tezos_baking.validators import Validator
import tezos_baking.validators as validators

# Global options

ballot_outcomes = {
    "yay": "Vote for accepting the proposal",
    "nay": "Vote for rejecting the proposal",
    "pass": "Submit a vote not influencing the result but contributing to quorum",
}

public_nodes = {
    "https://rpc.tzbeta.net": "by Tezos Foundation",
    "https://mainnet.api.tez.ie": "by ECAD Labs",
    "https://mainnet.smartpy.io": "by SmartPy",
    "https://teznode.letzbake.com": "by LetzBake!",
    "https://mainnet-tezos.giganode.io": "by GigaNode",
}

# Command line argument parsing

parser.add_argument(
    "--network",
    required=False,
    default="mainnet",
    help="Name of the network to vote on. Is 'mainnet' by default, "
    "but can be a testnet or the (part after @) name of any custom instance. "
    "For example, to use the tezos-baking-custom@voting service, input 'voting'. "
    "You need to already have set up the custom network using systemd services.",
)

parsed_args = parser.parse_args()


# Wizard CLI utility

welcome_text = """Tezos Voting Wizard

Welcome, this wizard will help you vote in the Tezos protocol amendment process.
Please note that to vote on mainnet, the minimum requirement is to have access
to a key that has voting rights, preferably through a connected ledger device.

All commands within the service are run under the 'tezos' user.

To access help and possible options for each question, type in 'help' or '?'.
Type in 'exit' to quit.
"""


# we don't need any data here, just a confirmation that a Tezos app is open
# `app_name` here can only be `"Wallet"` or `"Baking"`
def wait_for_ledger_app(app_name, client_dir):
    logging.info(f"Waiting for the ledger {app_name} app to be opened")
    print(f"Please make sure the Tezos {app_name} app is open on your ledger.")
    print(
        color(
            f"Waiting for the Tezos {app_name} app to be opened...",
            color_green,
        )
    )
    search_string = b"Found a Tezos " + bytes(app_name, "utf8")
    output = b""
    while re.search(search_string, output) is None:
        output = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} octez-client --base-dir {client_dir} list connected ledgers"
        ).stdout
        proc_call("sleep 1")


# Steps

new_proposal_query = Step(
    id="new_proposal_hash",
    prompt="Provide the hash for your newly submitted proposal.",
    default=None,
    help="The format is 'P[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{50}'",
    validator=Validator([validators.required_field, validators.protocol_hash]),
)

# We define this step as a function since the corresponding step requires that we get the
# proposal hashes off the chain.
# octez-client supports submitting up to 20 proposal hashes at a time, but it seems like this
# isn't recommended for use with Ledger, so we leave it at one hash pro query for now.
def get_proposal_period_hash(hashes):

    # if the chain is in the proposal period, it's possible to submit a new proposal hash
    extra_options = ["Specify new proposal hash"]

    return Step(
        id="chosen_hash",
        prompt="Select a proposal hash.\n"
        "You can choose one of the suggested hashes or provide your own:",
        help="You can submit one proposal at a time.\n"
        "'Specify new proposal hash' will ask a protocol hash from you. ",
        default=None,
        options=hashes + extra_options,
        validator=Validator(
            [
                validators.required_field,
                validators.enum_range(hashes + extra_options),
            ]
        ),
    )


ballot_outcome_query = Step(
    id="ballot_outcome",
    prompt="Choose the outcome for your ballot.",
    help="'yay' is for supporting the proposal, 'nay' is for rejecting the proposal,\n"
    "'pass' is used to not influence a vote but still contribute to reaching a quorum.",
    default=None,
    options=ballot_outcomes,
    validator=Validator(
        [validators.required_field, validators.enum_range(ballot_outcomes)]
    ),
)


def get_node_rpc_endpoint_query(network, default=None):
    url_path = "chains/main/blocks/head/header"
    node_is_alive = lambda host: url_is_reachable(mk_full_url(host, url_path))

    relevant_nodes = {
        url: provider
        for url, provider in public_nodes.items()
        if network == "mainnet" and node_is_alive(url)
    }
    return Step(
        id="node_rpc_endpoint",
        prompt="Provide the node's RPC address."
        if not relevant_nodes
        else "Choose one of the public nodes or provide the node's RPC address.",
        help="The node's RPC address will be used by octez-client to vote. If you have baking set up\n"
        "through systemd services, the address is usually 'http://localhost:8732' by default.",
        default="1" if relevant_nodes and default is None else default,
        options=relevant_nodes,
        validator=Validator(
            [
                validators.required_field,
                validators.any_of(
                    validators.enum_range(relevant_nodes),
                    validators.reachable_url(url_path),
                ),
            ]
        ),
    )


baker_alias_query = Step(
    id="baker_alias",
    prompt="Provide the baker's alias.",
    help="The baker's alias will be used by octez-client to vote. If you have baking set up\n"
    "through systemd services, the address is usually 'baker' by default.",
    default=None,
    validator=Validator([validators.required_field]),
)

# We define the step as a function to disallow choosing json
def get_key_mode_query(modes):
    return Step(
        id="key_import_mode",
        prompt="How do you want to import the voter key?",
        help="Tezos Voting Wizard will use the 'baker' alias for the key\n"
        "that will be used for voting. You will only need to import the key\n"
        "once unless you'll want to change the key.",
        options=modes,
        validator=Validator(validators.enum_range(modes)),
    )


class Setup(Setup):
    def check_baking_service(self):
        net = self.config["network"]
        try:
            proc_call(f"systemctl is-active --quiet tezos-baking-{net}.service")
            self.config["is_local_baking_setup"] = True
        except:
            print(f"No local baking services for {net} running on this machine.")
            print("If there should be, you can run 'tezos-setup' to set it up.")
            print()
            self.config["is_local_baking_setup"] = False
        finally:
            running = self.config["is_local_baking_setup"]
            logging.info(f"The baking services are {'' if running else 'not'} running")

    def check_data_correctness(self):
        logging.info("Querying data correctness")
        print("Baker data detected is as follows:")
        print(f"Data directory: {self.config['client_data_dir']}")
        print(f"Node RPC endpoint: {self.config['node_rpc_endpoint']}")
        print(f"Voter key: {self.config['baker_key_value']}")
        answer = yes_or_no("Does this look correct? (Y/n) ", "yes")
        logging.info(f"Answer is {answer}")
        return answer

    def search_client_config(self, field, default):
        logging.info("Searching client config")
        config_filepath = os.path.join(self.config["client_data_dir"], "config")
        if not os.path.isfile(config_filepath):
            return default
        else:
            return search_json_with_default(config_filepath, field, default)

    def collect_baking_info(self):
        logging.info("Collecting baking info")
        logging.info("Checking the local baking services")
        self.check_baking_service()
        if self.config.get("is_local_baking_setup", False):
            self.fill_baking_config()
            self.config["tezos_client_options"] = self.get_tezos_client_options()

            value, _ = get_key_address(
                self.config["tezos_client_options"], self.config["baker_alias"]
            )
            self.config["baker_key_value"] = value

            collected = self.check_data_correctness()
        else:

            network_dir = "/var/lib/tezos/client-" + self.config["network"]

            logging.info("Creating the network dir")
            proc_call(f"sudo -u tezos mkdir -p {network_dir}")

            print("With no tezos-baking.service running, this wizard will use")
            print(f"the default directory for this network: {network_dir}")

            self.config["client_data_dir"] = network_dir

            self.config["node_rpc_endpoint"] = self.search_client_config(
                "endpoint", None
            )
            if self.config["node_rpc_endpoint"] is None:
                self.query_and_update_config(
                    get_node_rpc_endpoint_query(self.config["network"])
                )

            key_import_modes.pop("json", None)
            self.get_baker_key()

            # Check correctness in case user wants to change this data upon reruns
            collected = self.check_data_correctness()

        while not collected:
            self.query_and_update_config(
                get_node_rpc_endpoint_query(
                    self.config["network"], self.config["node_rpc_endpoint"]
                )
            )

            replace_baker_key = self.check_baker_account()
            if replace_baker_key:
                key_mode_query = get_key_mode_query(key_import_modes)
                self.import_key(key_mode_query, "Wallet")

            collected = self.check_data_correctness()

    def get_baker_key(self):
        if "baker_alias" not in self.config:
            self.config["baker_alias"] = "baker"

        self.config["tezos_client_options"] = self.get_tezos_client_options()

        baker_key_value = get_key_address(
            self.config["tezos_client_options"], self.config["baker_alias"]
        )

        if baker_key_value is not None:
            value, _ = baker_key_value
            self.config["baker_key_value"] = value
        else:  # if there is no key with this alias, query import
            logging.info("No secret key found")
            key_mode_query = get_key_mode_query(key_import_modes)
            self.import_key(key_mode_query, "Wallet")

    def get_network(self):
        logging.info("Getting network")
        if parsed_args.network in networks.keys():
            self.config["network"] = parsed_args.network
        else:
            # TODO: maybe check/validate this
            self.config["network"] = "custom@" + parsed_args.network

    def fill_voting_period_info(self):
        logging.info("Filling in voting period info")
        logging.info("Getting voting period from octez-client")
        voting_proc = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} octez-client "
            f"{self.config['tezos_client_options']} show voting period"
        )
        if voting_proc.returncode == 0:
            info = voting_proc.stdout
        else:
            print_and_log("Couldn't get the voting period info.", logging.error)
            print("Please check that the network for voting has been set up correctly.")
            raise KeyboardInterrupt

        self.config["amendment_phase"] = (
            re.search(b'Current period: "(\\w+)"', info).group(1).decode("utf-8")
        )
        self.config["proposal_hashes"] = [
            phash.decode() for phash in re.findall(protocol_hash_regex, info)
        ]

    def process_proposal_period(self):
        logging.info("Processing proposal period")
        self.query_step(get_proposal_period_hash(self.config["proposal_hashes"]))

        hash_to_submit = self.config["chosen_hash"]
        if hash_to_submit == "Specify new proposal hash":
            self.query_step(new_proposal_query)
            hash_to_submit = self.config["new_proposal_hash"]

        logging.info("Submitting proposals")
        if self.check_ledger_use():
            print(
                color(
                    "Waiting for your response to the prompt on your Ledger Device...",
                    color_green,
                )
            )
        result = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} octez-client {self.config['tezos_client_options']} "
            f"submit proposals for {self.config['baker_alias']} {hash_to_submit}"
        )

        if result.returncode != 0:
            print()

            if re.search(b"[Ii]nvalid proposal", result.stderr) is not None:
                logging.error("The submitted proposal hash is invalid")
                print(color("The submitted proposal hash is invalid.", color_red))
                print("Check your custom submitted proposal hash and try again.")
                self.process_proposal_period()
                return
            elif re.search(b"Unauthorized proposal", result.stderr) is not None:
                logging.error("Cannot submit because of an unauthorized proposal.")
                print(
                    color(
                        "Cannot submit because of an unauthorized proposal.", color_red
                    )
                )
                print("This means you are not present in the voting listings.")
            elif re.search(b"Not in a proposal period", result.stderr) is not None:
                logging.error(
                    "Cannot submit because the voting period is no longer 'proposal'."
                )
                print(
                    color(
                        "Cannot submit because the voting period is no longer 'proposal'.",
                        color_red,
                    )
                )
                print("This means the voting period has already advanced.")
            elif re.search(b"Too many proposals", result.stderr) is not None:
                logging.error("Cannot submit because of too many proposals submitted.")
                print(
                    color(
                        "Cannot submit because of too many proposals submitted.",
                        color_red,
                    )
                )
                print("This means you have already submitted more than 20 proposals.")
            # No other "legitimate" proposal error ('empty_proposal', 'unexpected_proposal')
            # should be possible with the wizard, so we just raise an error with the whole output.
            else:
                logging.error("Something went wrong when calling octez-client")
                print(
                    "Something went wrong when calling octez-client. Please consult the logs."
                )
                raise OSError(result.stderr.decode())

            print("Please check your baker data and possibly try again.")

    def process_voting_period(self):
        logging.info("Processing voting period")
        print("The current proposal is:")
        # there's only one in any voting (exploration/promotion) period
        print(self.config["proposal_hashes"][0])
        print()

        self.query_step(ballot_outcome_query)

        logging.info("Submitting ballot")
        if self.check_ledger_use():
            print(
                color(
                    "Waiting for your response to the prompt on your Ledger Device...",
                    color_green,
                )
            )
        result = get_proc_output(
            f"sudo -u tezos {suppress_warning_text} octez-client {self.config['tezos_client_options']} "
            f"submit ballot for {self.config['baker_alias']} {self.config['proposal_hashes'][0]} "
            f"{self.config['ballot_outcome']}"
        )

        if result.returncode != 0:
            # handle the 'unauthorized ballot' error
            # Unfortunately, despite the error's description text, octez-client seems to use this error
            # both when the baker has already voted and when the baker was not in the voting listings
            # in the first place, so it's difficult to distinguish between the two cases.
            if re.search(b"Unauthorized ballot", result.stderr) is not None:
                logging.error("Cannot vote because of an unauthorized ballot")
                print()
                print(
                    color("Cannot vote because of an unauthorized ballot.", color_red)
                )
                print(
                    "This either means you have already voted or that you are not in the",
                    "voting listings in the first place.",
                )
                print("Please check your baker data and possibly try again.")
            if (
                re.search(b"Not in Exploration or Promotion period", result.stderr)
                is not None
            ):
                logging.error(
                    f"Cannot vote because the voting period is no longer '{self.config['amendment_phase']}'"
                )
                print()
                print(
                    color("Cannot vote because the voting period is", color_red),
                    color(f"no longer '{self.config['amendment_phase']}'.", color_red),
                )
                print(
                    "This most likely means the voting period has already advanced to the next one.",
                )
            # No other "legitimate" voting error ('invalid_proposal', 'unexpected_ballot')
            # should be possible with the wizard, so we just raise an error with the whole output.
            else:
                logging.error("Something went wrong when calling octez-client")
                print(
                    "Something went wrong when calling octez-client. Please consult the logs."
                )
                raise OSError(result.stderr.decode())

    def run_voting(self):

        print(welcome_text)

        self.get_network()

        self.collect_baking_info()

        self.config["tezos_client_options"] = self.get_tezos_client_options()

        # if a ledger is used for baking, ask to open Tezos Wallet app on it before proceeding
        if self.check_ledger_use():
            wait_for_ledger_app("Wallet", self.config["client_data_dir"])

        # process 'tezos-client show voting period'
        self.fill_voting_period_info()

        print_and_log(
            f"The amendment is currently in the {self.config['amendment_phase']} period."
        )
        if self.config["amendment_phase"] == "proposal":
            print(
                "Bakers can submit up to 20 protocol amendment proposals,",
                "including supporting existing ones.",
            )
            print()
            self.process_proposal_period()
        elif self.config["amendment_phase"] in ["exploration", "promotion"]:
            print(
                "Bakers can submit one ballot regarding the current proposal,",
                "voting either 'yay', 'nay', or 'pass'.",
            )
            print()
            self.process_voting_period()
        else:
            print_and_log("Voting isn't possible at the moment.")
            print_and_log("Exiting the Tezos Voting Wizard.")

        # if a ledger was used for baking on this machine, ask to open Tezos Baking app on it,
        # then restart the relevant baking service (due to issue: tezos/#4486)
        if self.config.get("is_local_baking_setup", False) and self.check_ledger_use():
            wait_for_ledger_app("Baking", self.config["client_data_dir"])
            net = self.config["network"]
            print_and_log(f"Restarting local {net} baking setup")
            proc_call(f"sudo systemctl restart tezos-baking-{net}.service")

        print()
        print("Thank you for voting!")
        logging.info("Exiting the Tezos Voting Wizard.")


def main():
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" ")

    try:
        setup_logger("tezos-vote.log")
        logging.info("Starting the Tezos Voting Wizard.")
        setup = Setup()
        setup.run_voting()
    except KeyboardInterrupt:
        print("Exiting the Tezos Voting Wizard.")
        logging.info(f"Received keyboard interrupt.")
        logging.info("Exiting the Tezos Voting Wizard.")
        sys.exit(1)
    except EOFError:
        print("Exiting the Tezos Voting Wizard.")
        logging.error(f"Reached EOF.")
        logging.info("Exiting the Tezos Voting Wizard.")
        sys.exit(1)
    except Exception as e:

        print_and_log(
            "Error in the Tezos Voting Wizard, exiting.",
            log=logging.error,
            colorcode=color_red,
        )

        log_exception(exception=e, logfile="tezos-vote.log")

        logging.info("Exiting the Tezos Voting Wizard.")
        sys.exit(1)


if __name__ == "__main__":
    main()

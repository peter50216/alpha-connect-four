# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import ttt_pb2 as ttt__pb2


class AIStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Play = channel.unary_unary(
                '/ttt.AI/Play',
                request_serializer=ttt__pb2.PlayRequest.SerializeToString,
                response_deserializer=ttt__pb2.PlayResponse.FromString,
                )


class AIServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Play(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_AIServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Play': grpc.unary_unary_rpc_method_handler(
                    servicer.Play,
                    request_deserializer=ttt__pb2.PlayRequest.FromString,
                    response_serializer=ttt__pb2.PlayResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'ttt.AI', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class AI(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Play(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ttt.AI/Play',
            ttt__pb2.PlayRequest.SerializeToString,
            ttt__pb2.PlayResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
